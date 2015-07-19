from gevent.monkey import patch_all
patch_all()

from gevent.pool import Pool

from datetime import datetime
import copy
import time
import logging

import pytz
import twython
from twython import Twython

from newslynx import settings
from newslynx.util import uniq
from newslynx.lib import embed


TWITTER_DATE_FORMAT = '%a %b %d %H:%M:%S +0000 %Y'

log = logging.getLogger(__name__)


class Twitter(object):

    """
    utilities for coercing twitter data into newsylnx formats.
    """

    incl_embed = False

    default_kws = {
        'since_id': None,
        'throttle': 15,
        'count': 200,
        'max_requests': 2,
        'num_workers': 20,
        'wait': 1,
        'backoff': 2,
        'timeout': 10
    }

    def connect(self, **auth):
        """
        Given environment variables / auth, connect to twitter's api
        """
        self.conn = Twython(
            app_key=auth.get('app_key', settings.TWITTER_API_KEY),
            app_secret=auth.get('app_secret', settings.TWITTER_API_SECRET),
            oauth_token=auth.get('oauth_token'),
            oauth_token_secret=auth.get('oauth_token_secret'),
            access_token=auth.get('access_token', None)
        )

    def list_to_event(self, **kw):
        """
        Fetch a list timeline
        """
        tweets = self._paginate(self.conn.get_list_statuses, **kw)
        pool = Pool(kw.get('num_workers'))
        for event in pool.imap_unordered(self.to_event, tweets):
            yield event

    def search_to_event(self, **kw):
        """
        Search twitter.
        """
        tweets = self._paginate(self.conn.search, **kw)
        pool = Pool(kw.get('num_workers'))
        for event in pool.imap_unordered(self.to_event, tweets):
            yield event

    def user_to_event(self, **kw):
        """
        Get a user's feed.
        """
        tweets = self._paginate(self.conn.get_user_timeline, **kw)
        pool = Pool(kw.get('num_workers'))
        for event in pool.imap_unordered(self.to_event, tweets):
            yield event

    def to_event(self, tweet, **kw):
        """
        Parse a tweet into a newslynx event.
        """
        t = TwitterEvent(**tweet)
        t.incl_embed = copy.copy(self.incl_embed)
        return t.to_dict()

    def _paginate(self, func, **kw):
        """
        Paginate through the api, catching errors
        and stopping if we finish or reach
        `max_requests`
        """
        defs = copy.copy(self.default_kws)
        defs.update(kw)
        kw = defs

        # if we passed in a `max_id`,
        # decrement it by 1
        if kw['since_id']:
            kw['since_id'] = kw['since_id'] - 1
        else:
            kw.pop('since_id', None)

        # set control variables
        p = 1

        # hit the api until we should stop
        while True:

            # run the function first
            tweets = self._catch_err(func, **kw)

            # catch search results
            if 'statuses' in tweets:
                tweets = tweets.get('statuses')

            # get the max id
            since_id = self._get_since_id(tweets)

            # if we got a since_id, proceed
            if not since_id:
                break

            # update since_id kwarg
            kw['since_id'] = since_id - 1

            # iterate through tweets
            for t in tweets:
                yield t

            # if we've reached the max number of pages, break
            max_requests = kw.get('max_requests')
            if max_requests and p >= max_requests:
                break

            # increment page
            p += 1

            # throttle requests
            time.sleep(kw.get('throttle'))

    def _get_since_id(self, tweets):
        """
        Get the max id for a response
        """

        ids = [t['id'] for t in tweets if t and 'id' in t]

        if len(ids) == 0:
            return None
        max_id = sorted(ids)[0]
        return max_id

    def _catch_err(self, func, **kw):
        """
        Catch Twitter API Errors, backoff, and timeout.
        """

        # get timing kwargs
        wait = kw.get('wait')
        backoff = kw.get('backoff')
        timeout = kw.get('timeout')

        # try until we timeout
        t0 = time.time()
        while True:
            try:
                tweets = func(**kw)
                break

            # backoff from errors
            except twython.exceptions.TwythonError as e:
                time.sleep(wait)
                wait *= backoff

                # timeout
                now = time.time()
                if now - t0 > timeout:
                    err_msg = "Timing out beacause of {0}"\
                              .format(e.message)
                    raise Exception(err_msg)
        return tweets


class TwitterEvent(object):

    """
    Parses a tweet into  Newslynx Event
    """

    incl_embed = False

    def __init__(self, **tweet):

        # get nested dicts
        self._entities = tweet.get('entities', {})
        self._user = tweet.get('user')
        self._tweet = tweet

    @property
    def source_id(self):
        return self._tweet.get('id_str', None)

    @property
    def url(self):
        return "http://twitter.com/{}/statuses/{}"\
            .format(self.authors[0], self.source_id)

    @property
    def body(self):
        return self._tweet.get('text', '').encode('utf-8')

    @property
    def embed(self):
        return embed.twitter(self.url)

    @property
    def authors(self):
        sn = self._user.get('screen_name', None)
        if not sn:
            return []
        return [sn]

    @property
    def created(self):
        c = self._tweet.get('created_at', None)
        if c:
            c = datetime.strptime(c, TWITTER_DATE_FORMAT)
            return c.replace(tzinfo=pytz.utc)
        return None

    @property
    def img_url(self):
        media = uniq([h['media_url'] for h in self._entities.get('media', [])])
        if len(media):
            return media[0]
        return self._user.get('profile_image_url', None)

    @property
    def links(self):
        return uniq([u['expanded_url'] for u in self._entities.get('urls', [])])

    @property
    def meta(self):
        d = {
            'followers': self._user.get('followers_count'),
            'friends': self._user.get('friends_count'),
            'hashtags': uniq([h['text'] for h in self._entities.get('hashtags', [])])
        }
        if self.incl_embed:
            d['embed'] = self.embed
        return d

    def to_dict(self):
        return {
            'source_id': self.source_id,
            'url': self.url,
            'img_url': self.img_url,
            'body': self.body,
            'created': self.created,
            'authors': self.authors,
            'links': self.links,
            'meta': self.meta
        }
