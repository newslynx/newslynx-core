
from newslynx.core import rdb
from newslynx import settings
from newslynx.lib import url
from newslynx.lib.serialize import (
    obj_to_json, json_to_obj)


class URLCache(object):

    """
    A redis cache of raw_url > normalized url
    """

    def __init__(self, **kw):
        self.key_prefix = kw.get('key_prefix', settings.URL_CACHE_KEY_PREFIX)
        self.ttl = kw.get('ttl', settings.URL_CACHE_TTL)
        self.rdb = rdb

    def get_cache(self, raw_url):
        """
        Standardize + cache a raw url
        returning it's standardized url + global bitly url.
        """
        key = self._format_key(raw_url)
        url = self.rdb.get(key)

        if not url:

            # standradize the url
            url = url.prepare(raw_url)

            # don't fail.
            if not url:
                url = raw_url

            self.rdb.set(key, url, ex=self.ttl)

        return url
