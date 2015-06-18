"""
All things related to counting shares for urls.

NOTE: All urls should be canonicalized before using these methods.

This code was adapted from: https://github.com/debrouwere/social-shares
"""

from gevent.monkey import patch_all
patch_all()
from gevent.pool import Pool

from copy import copy

import requests

from newslynx.lib import network
from newslynx.lib.serialize import json_to_obj, obj_to_json


ALL_SOURCES = [
    'twitter', 'facebookfql', 'reddit', 'linkedin',
    'facebook', 'pinterest', 'googleplus'
]

DEFAULT_SOURCES = [
    'twitter', 'facebookfql', 'reddit', 'linkedin',
    'pinterest'
]


class ShareCount(object):

    """
    An abstract class to inherit from. The idea is that
    you should only have to set
     - the endpoint
     -  a function to format the parameters to pass to it
     -  a funciton to parse the data.

    All parse functions should return a flat dictionary.
    """
    endpoint = None

    def format_params(self, url):
        """
        Default to most common.
        """
        return {'url': url, 'format': 'json'}

    def fetch(self, params):
        """
        Fetch the data.
        """
        return network.get_json(self.endpoint, **params)

    def parse(self, data):
        """
        Your custom parsing function.
        """
        raise NotImplemented

    def count(self, url):
        """
        The main function.
        """
        params = self.format_params(url)
        data = self.fetch(params)
        if not data:
            return {}
        return self.parse(data)


# class Delicious(ShareCount):

#     endpoint = 'http://feeds.delicious.com/v2/json/urlinfo/data'

#     def parse(self, data):
#         if not len(data):
#             return {'delicious_shares': 0}

#         return {
#             'delicious_shares': data[0]['count'],
#         }


class Facebook(ShareCount):

    endpoint = 'https://graph.facebook.com/'

    def format_params(self, url):
        return {'id': url}

    def parse(self, data):
        return {
            'facebook_shares': data['shares']
        }


class FacebookFQL(ShareCount):

    endpoint = 'https://graph.facebook.com/fql'
    query = """SELECT comment_count, like_count, share_count
               FROM link_stat WHERE url = \"{}\"
            """

    def format_params(self, url):
        return {'q': self.query.format(url)}

    def parse(self, data):
        if not len(data):
            return {}
        return {
            'facebook_likes': data['data'][0]['like_count'],
            'facebook_shares': data['data'][0]['share_count'],
            'facebook_comments': data['data'][0]['comment_count']
        }


class LinkedIn(ShareCount):

    endpoint = 'http://www.linkedin.com/countserv/count/share'

    def parse(self, data):
        return {
            'linkedin_shares': data['count']
        }


class Pinterest(ShareCount):

    endpoint = 'http://api.pinterest.com/v1/urls/count.json'

    # override the fetch method to handle jsonp
    def fetch(self, params):
        text = network.get(self.endpoint, **params)
        if not text:
            return None
        return self._parse_jsonp(text)

    def parse(self, data):
        return {
            'pinterest_shares': data['count']
        }

    def _parse_jsonp(self, text):
        if not '(' in text:
            return None
        start = text.index('(') + 1
        stop = text.rindex(')')
        return json_to_obj(text[start:stop])


class Reddit(ShareCount):

    endpoint = 'http://buttons.reddit.com/button_info.json'

    def parse(self, data):

        ups = 0
        downs = 0
        for child in data['data']['children']:
            ups += child['data']['ups']
            downs += child['data']['downs']

        return {
            'reddit_upvotes': ups,
            'reddit_downvotes': downs
        }


class Twitter(ShareCount):

    endpoint = 'http://urls.api.twitter.com/1/urls/count.json'

    def parse(self, data):
        return {
            'twitter_shares': data['count']
        }


class GooglePlus(ShareCount):

    endpoint = 'https://clients6.google.com/rpc'

    def format_params(self, url):
        return obj_to_json({
            'method': 'pos.plusones.get',
            'id': 'p',
            'key': 'p',
            'params': {
                'nolog': True,
                'id': url,
                'source': 'widget',
            },
            'jsonrpc': '2.0',
            'apiVersion': 'v1'
        })

    def fetch(self, body):
        try:
            r = requests.post(self.endpoint, data=body)
            return r.json()
        except Exception:
            return None

    def parse(self, data):
        cnt = int(data['result']['metadata']['globalCounts']['count'])
        return {
            'googleplus_shares': cnt
        }


class ShareCounts(object):

    """
    A class with all methods.
    """

    def __init__(self):
        self.twitter = Twitter().count
        self.facebook = Facebook().count
        self.facebookfql = FacebookFQL().count
        # self.delicious = Delicious().count
        self.reddit = Reddit().count
        self.pinterest = Pinterest().count
        self.linkedin = LinkedIn().count
        self.googleplus = GooglePlus().count


def count(url, sources='all'):
    """
    Count shares for multiple sources.
    """
    # init class
    sc = ShareCounts()

    # listify
    if not isinstance(sources, list):
        sources = [sources]

    # get all
    if 'all' in sources:
        sources = copy(ALL_SOURCES)

    # if both facebook and facebookfql are included
    # only use facebookfql
    if 'facebook' in sources and 'facebookfql' in sources:
        sources.remove('facebook')

    # check sources.
    for source in sources:
        if source not in ALL_SOURCES:
            raise ValueError(
                'Source "{}" is not supported.'
                .format(source))

    # count fx
    def _count(source):
        fx = getattr(sc, source)
        return fx(url)

    # single source
    n_sources = len(sources)
    if n_sources == 1:
        return _count(sources[0])

    # multiple
    p = Pool(n_sources)

    # output
    data = {}
    for obj in p.imap_unordered(_count, sources):
        data.update(obj)

    return data
