"""
Abstract wrappers around ingest modules.

Allows for submitting ingest jobs to a queue and
chunking execution.
"""

import gevent
import gevent.monkey
gevent.monkey.patch_all()
from gevent.pool import Pool

import time
from traceback import format_exc
from functools import partial

from rq.timeouts import JobTimeoutException

from newslynx.core import queues, rds
from newslynx.exc import (
    RequestError, InternalServerError)
from newslynx.util import gen_uuid
from newslynx.tasks import ingest
from newslynx.lib.serialize import (
    pickle_to_obj, obj_to_pickle,
    json_to_obj, obj_to_json)
from newslynx import util


MAX_CHUNK_SIZE = 250
MAX_WORKERS = 5


def content(data, **kw):
    """
    Bulk load content
    """
    kw.setdefault('q_timeout', 300)
    kw.setdefault('q_max_workers', )
    kw.setdefault('q_chunk_size', 50)
    kw.setdefault('q_src', 'content')
    return bulkload(data, **kw)


def events(data, **kw):
    """
    Bulk load events
    """
    kw.setdefault('q_timeout', 500)
    kw.setdefault('q_max_workers', )
    kw.setdefault('q_chunk_size', 100)
    kw.setdefault('q_src', 'events')
    return bulkload(data, **kw)


def content_timeseries(data, **kw):
    """
    Bulk load content timeseries.
    """
    kw.setdefault('q_timeout', 180)
    kw.setdefault('q_max_workers', )
    kw.setdefault('q_chunk_size', 200)
    kw.setdefault('q_src', 'content_timeseries')
    return bulkload(data, **kw)


def content_summary(data, **kw):
    """
    Bulk load content summaries.
    """
    kw.setdefault('q_timeout', 180)
    kw.setdefault('q_max_workers', )
    kw.setdefault('q_chunk_size', 200)
    kw.setdefault('q_src', 'content_summary')
    return bulkload(data, **kw)


def org_timeseries(data, **kw):
    """
    Bulk load org timeseries
    """
    kw.setdefault('q_timeout', 180)
    kw.setdefault('q_max_workers', )
    kw.setdefault('q_chunk_size', 200)
    kw.setdefault('q_src', 'org_timeseries')
    return bulkload(data, **kw)


def org_summary(data, **kw):
    """
    Bulk load org timeseries
    """
    kw.setdefault('q_timeout', 60)
    kw.setdefault('q_max_workers', )
    kw.setdefault('q_chunk_size', 200)
    kw.setdefault('q_src', 'org_summary')
    return bulkload(data, **kw)


def bulkload(data, **kw):
    """
    Bulk Load any data.
    """
    kw['src'] = kw.pop('q_src', kw.pop('src', None))
    if not kw['src']:
        raise ValueError('Missing src.')

    job_id = gen_uuid()

    # set queue defaults
    qkw = dict(
        queued=kw.pop('queued', True),
        job_id=job_id,
        timeout=kw.pop('q_timeout', 1000),
        serializer=kw.pop('q_serializer', 'json'),
        result_ttl=kw.pop('q_result_ttl', 60),
        kwargs_ttl=kw.pop('q_kwargs_ttl', 120),
        name=kw.pop('q_name', 'bulk'),
        max_workers=kw.pop('q_max_workers', MAX_WORKERS),
        job_key_fmt=kw.pop('q_job_key', 'rq:{src}:bulk:'.format(**kw)+"{}"),
        chunk_size=kw.pop('q_chunk_size', MAX_CHUNK_SIZE)
    )
    kw.update({'queued': qkw.get('queued', True)})

    # if this is not a queued job, just run ingest.
    if not qkw.get('queued'):
        return ingest.source(data, **kw)

    q = queues.get(qkw.pop('name', 'bulk'))

    # store the data + kwargs in redis temporarily
    # this makes the enqueuing process much, much more
    # efficient by allowing us to only pass a single key
    # into the queue rather than a massive dump of data
    # however it also means that all kwargs must be
    # json serializable
    job_key = qkw['job_key_fmt'].format(job_id)
    job = {'data': data, 'kw': kw}

    if qkw['serializer'] == 'json':
        job = obj_to_json(job)

    elif qkw['serializer'] == 'pickle':
        job = obj_to_pickle(job)

    rds.set(job_key, job, ex=qkw['kwargs_ttl'])

    q.enqueue(bulkworker, job_id, **qkw)
    return job_id


def bulkworker(job_id, **qkw):
    """
    Fetch a job and execute it.
    """
    start = time.time()
    try:
        k = qkw['job_key_fmt'].format(job_id)
        job = rds.get(k)
        if not job:
            raise InternalServerError(
                'An unexpected error occurred while processing bulk upload.'
            )

        if qkw['serializer'] == 'json':
            job = json_to_obj(job)

        elif qkw['serializer'] == 'pickle':
            job = pickle_to_obj(job)

        data = job.pop('data', [])
        job = job.pop('kw', {})

        # delete them
        rds.delete(k)

        # chunk list
        chunked_data = util.chunk_list(data, qkw.get('chunk_size'))

        # partial funtion
        load_fx = partial(ingest.source, **job)

        # pooled execution
        pool = Pool(qkw.get('max_workers', MAX_WORKERS))

        for res in pool.imap_unordered(load_fx, chunked_data):
            pass
        return True

    except Exception:
        tb = format_exc()
        raise RequestError('An Error Ocurred while running {}:\n{}'.format(job_id, tb))

    except JobTimeoutException:
        end = time.time()
        raise InternalServerError(
            'Bulk loading timed out after {} seconds'
            .format(end-start))


