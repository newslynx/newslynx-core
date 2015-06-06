
from newslynx.core import rds
from newslynx import settings
from newslynx.lib.url import prepare, is_abs


class URLCache(object):

    """
    A redis cache of raw_url > normalized url
    """

    def __init__(self, **kw):
        self.key_prefix = kw.get('key_prefix', settings.URL_CACHE_PREFIX)
        self.ttl = kw.get('ttl', settings.URL_CACHE_TTL)
        self.rds = rds

    def _format_key(self, raw_url):
        return self.key_prefix + ":" + raw_url

    def get(self, raw_url):
        """
        Standardize + cache a raw url
        returning it's standardized url + global bitly url.
        """
        key = self._format_key(raw_url)
        url = self.rds.get(key)

        if not url:

            # standradize the url
            if is_abs(raw_url):
                source = raw_url
            else:
                source = None
            url = prepare(raw_url, source=source)

            # don't fail.
            if not url:
                url = raw_url

            # shorten
            # self.rds.set(key, url, ex=self.ttl)

        return url

url_cache = URLCache()
