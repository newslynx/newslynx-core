
from newslynx.core import rdb
from newslynx import settings
from newslynx.lib import url
from newslynx.lib.serialize import (
    obj_to_json, json_to_obj)
from newslynx.models import Thing, Event


class URLCache(object):
    """
    A redis cache of > normalized urls / story ids
    """

    def __init__(self, **kw):
        self.key_prefix = kw.get('key_prefix': settings.URL_CACHE_KEY_PREFIX)
        self.ttl = kw.get('ttl', settings.URL_CACHE_TTL)
        self.rdb = rdb

    def _format_key(self, raw_url):
        """
        Format the key for redis
        """
        return "{}:{}".format(self.std_key_prefix, raw_url)

    def _format_short_key(self, raw_url):
        """
        Format the key for redis
        """
        return "{}:{}".format(self.short_key_prefix, raw_url)

    def get_cache(self, raw_url):
        """
        Standardize + cache a raw url
        returning it's standardized url + global bitly url.
        """
        key = self._format_key(raw_url)
        standard_url = self.rdb.get(key)
        if not standard_url:
            standard_url = url.prepare(raw_url)
            if not standard_url:
                return raw_url
            self.

    def short_url(self, raw_url):
        """
        Shorten + cache a raw url, returning it's global bitly url.
        """
        key = self._format_short_key(raw_url)
        standard_url = self.rdb.get(key)
        if not standard_url:
            standard_url = url.prepare(raw_url)
            if not standard_url:
                return raw_url
            self.


