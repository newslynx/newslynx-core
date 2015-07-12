import gevent
import gevent.monkey
gevent.monkey.patch_all()

from datetime import timedelta
from random import choice
import requests
import time

from newslynx.client import API
from newslynx.lib import dates
from newslynx.lib import rss
from newslynx.models import (
    ExtractCache, URLCache, ThumbnailCache)

api = API(org=1, raise_errors=True)

# # flush the cache to ensure realstic times.
# URLCache.flush()
# ExtractCache.flush()
# ThumbnailCache.flush()


def poll_status_url(status_url):
    """
    Pool a job's status url.
    """
    time.sleep(2)
    while True:
        r = requests.get(status_url)
        time.sleep(1)
        d = r.json()
        print d
        if d['status'] == 'success':
            print "STATUS: {status} FROM {orig_url}".format(**d)
            break
        elif d['status'] == 'error':
            print "STATUS: {status} FROM {orig_url}".format(**d)
            raise Exception(d.get('message', ''))
        else:
            print "STATUS: {status} FROM {orig_url}".format(**d)


def test_bulk_content_timeseries(nrows=10000):
    """
    Test bulk loading timeseries metrics
    """
    start = time.time()
    content_item_ids = [r['id'] for r in api.orgs.simple_content()]
    data = []
    for i in xrange(nrows):
        hours = nrows - i
        data.append({
            'content_item_id': choice(content_item_ids),
            'datetime': (dates.now() - timedelta(days=30, hours=hours)).isoformat(),
            'metrics': {'twitter_shares': i}
        })

    # make request and return status url
    res = api.content.bulk_create_timeseries(data)
    poll_status_url(res.get('status_url'))
    end = time.time()
    print "Bulk Loading {} Content Timeseries Metrics Took {} seconds"\
        .format(nrows, round((end-start), 2))


def test_bulk_content_summary(nrows=1000):
    """
    Test bulk loading summary metrics.
    """
    start = time.time()
    content_item_ids = [r['id'] for r in api.orgs.simple_content()]
    data = []
    for i in xrange(nrows):
        data.append({
            'content_item_id': choice(content_item_ids),
            'metrics': {'twitter_shares': i}
        })

    # make request and return status url
    res = api.content.bulk_create_summary(data)
    poll_status_url(res.get('status_url'))
    end = time.time()
    print "Bulk Loading {} Content Summary Metrics Took {} seconds"\
        .format(nrows, round((end-start), 2))


def test_bulk_org_timeseries(nrows=1000):
    """
    Test bulk loading org timeseries metrics.
    """
    start = time.time()
    data = []
    for i in xrange(nrows):
        hours = i
        data.append({
            'metrics': {'ga_pageviews': i},
            'datetime': (dates.now() - timedelta(days=30, hours=hours)).isoformat()
        })

    # make request and return status url
    res = api.orgs.bulk_create_timeseries(data=data)
    poll_status_url(res.get('status_url'))
    end = time.time()
    print "Bulk Loading {} Org Timeseries Metrics Took {} seconds"\
        .format(nrows, round((end-start), 2))


def test_bulk_content_items(feed_url='http://feeds.propublica.org/propublica/main', domains=['propublica.org']):
    """
    Parse an rss feed and bulk create content items via article extraction.
    """
    data = []
    for entry in rss.get_entries(feed_url, domains):
        entry['type'] = 'article'
        if entry.get('url'):
            data.append(entry)

    start = time.time()
    # make request and return status url
    res = api.content.bulk_create(data=data)
    poll_status_url(res.get('status_url'))
    end = time.time()
    print "Bulk Loading {} Content Items Took {} seconds"\
        .format(len(data), round((end-start), 2))



def test_bulk_events(feed_url='http://feeds.propublica.org/propublica/main', domains=['propublica.org']):
    """
    Parse an rss feed and bulk create events.
    """
    data = []
    for entry in rss.get_entries(feed_url, domains):
        entry['type'] = 'article'
        if entry.get('url'):
            data.append(entry)
    start = time.time()
    # make request and return status url
    res = api.events.bulk_create(data)
    poll_status_url(res.get('status_url'))
    end = time.time()
    print "Bulk Loading {} Events Took {} seconds"\
        .format(len(data), round((end-start), 2))

if __name__ == '__main__':
    test_bulk_events()
