import gevent
import gevent.monkey
gevent.monkey.patch_all()
from gevent.pool import Pool

import time

from functools import partial
from rq.timeouts import JobTimeoutException

from newslynx.core import queues, db
from newslynx.core import rds, gen_session
from newslynx.exc import (
    RequestError, InternalServerError)
from newslynx.util import gen_uuid
from newslynx.lib.serialize import (
    pickle_to_obj, obj_to_pickle)

from . import ingest_content_item
from . import ingest_event
from . import ingest_metric


class BulkLoader(object):

    __module__ = 'newslynx.tasks.bulk'

    returns = None  # either "model" or "query"
    timeout = 1000  # seconds
    result_ttl = 60  # seconds
    kwargs_ttl = 1000  # in case there is a backup in the queue
    max_workers = 7
    concurrent = True
    kwargs_key = 'rq:kwargs:{}'
    q = queues.get('bulk')
    redis = rds

    def load_one(self, item, **kw):
        """
        The method to overwrite.
        """
        raise NotImplemented

    def _load_one(self, item, **kw):
        """
        A wrapper which will catch errors
        and bubble them up
        """
        try:
            return self.load_one(item, **kw)
        except Exception as e:
            return Exception(e.message)

    def _handle_errors(self, errors):
        if not isinstance(errors, list):
            errors = [errors]
        return RequestError(
            'There was an error while bulk uploading: '
            '{}'.format(errors[0].message))

    def load_all(self, kwargs_key):
        """
        Do the work.
        """
        start = time.time()
        try:
            # create a session specific to this task
            session = gen_session()

            # get the inputs from redis
            kwargs = self.redis.get(kwargs_key)
            if not kwargs:
                raise InternalServerError(
                    'An unexpected error occurred while processing bulk upload.'
                )

            kwargs = pickle_to_obj(kwargs)
            data = kwargs.get('data')
            kw = kwargs.get('kw')

            # delete them
            self.redis.delete(kwargs_key)

            outputs = []
            errors = []

            fx = partial(self._load_one, **kw)

            if self.concurrent:
                pool = Pool(min([len(data), self.max_workers]))
                for res in pool.imap_unordered(fx, data):
                    if isinstance(res, Exception):
                        errors.append(res)
                    else:
                        outputs.append(res)
            else:
                for item in data:
                    res = fx(item)
                    if isinstance(res, Exception):
                        errors.append(res)
                    else:
                        outputs.append(res)

            # return errors
            if len(errors):
                self._handle_errors(errors)

            # add objects and execute
            if self.returns == 'model':
                for o in outputs:
                    if o is not None:
                        try:
                            session.add(o)
                            session.commit(o)
                        except Exception as e:
                            self._handle_errors(e)

            # union all queries
            elif self.returns == 'query':
                for query in outputs:
                    if query is not None:
                        try:
                            session.execute(query)
                        except Exception as e:
                            self._handle_errors(e)

            try:
                session.commit()

            except Exception as e:
                session.rollback()
                session.remove()
                self._handle_errors(e)

            # return true if everything worked.
            session.close()
            return True

        except JobTimeoutException:
            end = time.time()
            return InternalServerError(
                'Bulk loading timed out after {} seconds'
                .format(end-start))

    def run(self, data, **kw):

        # store the data + kwargs in redis temporarily
        # this makes the enqueuing process much, much more
        # efficient by allowing us to only pass a single key
        # into the queue rather than a massive dump of data
        # however it also means that all kwargs must be
        # json serializable
        job_id = gen_uuid()
        kwargs_key = self.kwargs_key.format(job_id)
        kwargs = {'data': data, 'kw': kw}
        self.redis.set(kwargs_key, obj_to_pickle(kwargs), ex=self.kwargs_ttl)

        # send the job to the task queue
        self.q.enqueue(
            self.load_all, kwargs_key,
            job_id=job_id, timeout=self.timeout,
            result_ttl=self.result_ttl)

        return job_id


class ContentTimeseriesBulkLoader(BulkLoader):

    returns = 'query'
    timeout = 240

    def load_one(self, item, **kw):
        return ingest_metric.content_timeseries(item, **kw)


class ContentSummaryBulkLoader(BulkLoader):

    returns = 'query'
    timeout = 480

    def load_one(self, item, **kw):
        return ingest_metric.content_summary(item, **kw)


class OrgTimeseriesBulkLoader(BulkLoader):

    returns = 'query'
    timeout = 240

    def load_one(self, item, **kw):
        return ingest_metric.org_timeseries(item, **kw)


class EventBulkLoader(BulkLoader):

    returns = 'model'
    timeout = 480

    def load_one(self, item, **kw):
        return ingest_event.ingest(item, **kw)


class ContentItemBulkLoader(BulkLoader):

    returns = 'model'
    timeout = 240

    def load_one(self, item, **kw):
        return ingest_content_item.ingest(item, **kw)


# make sure the functions are importable + pickleable
content_timeseries = ContentTimeseriesBulkLoader().run
content_summary = ContentSummaryBulkLoader().run
org_timeseries = OrgTimeseriesBulkLoader().run
events = EventBulkLoader().run
content_items = ContentItemBulkLoader().run
