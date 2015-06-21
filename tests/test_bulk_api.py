import gevent
import gevent.monkey
gevent.monkey.patch_all()

from datetime import timedelta
from random import choice
import time

from newslynx.client import API
from newslynx.models import ExtractCache, URLCache, ThumbnailCache
from newslynx.lib import dates
from newslynx.lib import rss
import requests

api = API(org=1)

# # flush the cache to ensure realstic times.
# URLCache.flush()
# ExtractCache.flush()
# ThumbnailCache.flush()


def poll_status_url(status_url):
    """
    Pool a job's status url.
    """
    while True:
        r = requests.get(status_url)
        time.sleep(1)
        r = r.json()
        if r['status'] == 'success':
            print "STATUS: {}".format(r['status'])
            break
        elif r['status'] == 'error':
            print "STATUS: {}".format(r['status'])
            raise Exception(r.get('message', ''))
        else:
            print "STATUS: {}".format(r['status'])


def test_bulk_content_timeseries(nrows=10000):
    """
    Test bulk loading timeseries metrics
    """
    start = time.time()

    data = []
    for i in xrange(nrows):
        hours = nrows - i
        data.append({
            'content_item_id': choice(range(1, 50)),
            'datetime': (dates.now() - timedelta(days=30, hours=hours)).isoformat(),
            'metrics': {'twitter_shares': i}
        })

    # make request and return status url
    res = api.content.bulk_create_timeseries(data=data)
    poll_status_url(res.get('status_url'))
    end = time.time()
    print "Bulk Loading {} Timeseries Metrics Took {} seconds"\
        .format(nrows, round((end-start), 2))


def test_bulk_content_items(feed_url='http://feeds.propublica.org/propublica/main', domains=['propublica.org']):
    """
    Parse an rss feed and bulk create content items via article extraction.
    """
    data = []
    for entry in rss.get_entries(feed_url, domains):
        entry['type'] = 'article'
        if entry.get('url'):
            entry.pop('links', None)
            data.append(entry)

    start = time.time()
    # make request and return status url
    res = api.content.bulk_create(data=data, extract=True)
    poll_status_url(res.get('status_url'))
    end = time.time()
    print "Bulk Loading {} Content Items Took {} seconds"\
        .format(len(data), round((end-start), 2))

if __name__ == '__main__':
    gevent.joinall([
        gevent.spawn(test_bulk_content_items),
        gevent.spawn(test_bulk_content_timeseries)
    ])
