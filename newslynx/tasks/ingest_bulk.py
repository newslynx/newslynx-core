import gevent.monkey
gevent.monkey.patch_all()
from gevent.pool import Pool
import time

from newslynx.core import bulk_queue
from newslynx.core import db
from newslynx.exc import RequestError
from newslynx.tasks.ingest_content_item import ingest_content_item
from newslynx.tasks.ingest_event import ingest_event
from newslynx.tasks import ingest_metric
from newslynx.util import gen_uuid


class BulkLoader(object):
    __module__ = 'newslynx.tasks.bulk'
    returns = None  # either "model" or "query"
    timeout = 1000

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
            return False, self.load_one(item, **kw)
        except Exception as e:
            return True, e

    def load_all(self, data, **kw):
        """
        Do the work.
        """
        outputs = []
        errors = []
        pool = Pool(min([len(data), 10]))

        # pooled execution
        for err, res in pool.imap_unordered(self._load_one, data):
            time.sleep(10)
            if err:
                errors.append(res)
            else:
                outputs.append(res)

        # return errors
        if len(errors):
            return RequestError(
                'There were errors while bulk uploading: '
                '{}'.format("\n".join([e.message for e in errors]))
            )

        # add objects and execute
        if self.returns == 'model':
            for i, o in enumerate(outputs):
                db.session.add(o)

        # union all queries
        elif self.returns == 'query':
            query = " UNION ALL ".join(outputs)
            db.session.execute(query)

        try:
            db.session.commit()
        except Exception as e:
            return RequestError(
                'There were errors while bulk uploading: {}'
                .format(e.message))
        return True

    def run(self, data, **kw):
        """
        Excecute the job in the queue and return the key id.
        """
        job_id = gen_uuid()
        result = bulk_queue.enqueue(
            self.load_all, data, timeout=self.timeout, job_id=job_id, **kw)
        return job_id


class ContentTimeseriesBulkLoader(BulkLoader):

    returns = 'query'
    timeout = 240

    def load_one(self, item, **kw):

        return ingest_metric.content_timeseries(item, **kw)


class ContentSummaryBulkLoader(BulkLoader):

    returns = 'query'
    timeout = 120

    def load_one(self, item, **kw):

        return ingest_metric.content_summary(item, **kw)


class OrgTimeseriesBulkLoader(BulkLoader):

    returns = 'query'
    timeout = 240

    def load_one(self, item, **kw):

        return ingest_metric.org_timeseries(item, **kw)


class OrgSummaryBulkLoader(BulkLoader):

    returns = 'query'
    timeout = 120

    def load_one(self, item, **kw):

        return ingest_metric.org_summary(item, **kw)


class EventBulkLoader(BulkLoader):

    returns = 'model'
    timeout = 120

    def load_one(self, item, **kw):

        return ingest_event(item, **kw)


class ContentItemBulkLoader(BulkLoader):

    returns = 'model'
    timeout = 120

    def load_one(self, item, **kw):

        return ingest_content_item(item, **kw)


# make these easily importable.
conent_timeseries = ContentTimeseriesBulkLoader().run
content_summary = ContentSummaryBulkLoader().run
org_timeseries = OrgTimeseriesBulkLoader().run
org_summary = OrgSummaryBulkLoader().run
events = EventBulkLoader().run
content_items = ContentItemBulkLoader().run
