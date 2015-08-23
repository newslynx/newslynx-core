from newslynx.core import settings
from newslynx.lib import url
from newslynx.lib import article
from newslynx.lib import image

from .cache import Cache


class URLCache(Cache):

    """
    A redis cache of raw_url > normalized url
    """
    key_prefix = settings.URL_CACHE_PREFIX
    ttl = settings.URL_CACHE_TTL

    def work(self, raw_url):
        """
        Standardize + cache a raw url
        returning it's standardized url + global bitly url.
        """
        # standradize the url
        if url.is_abs(raw_url):
            source = raw_url
        else:
            source = None
        return url.prepare(raw_url, source=source, canonicalize=True, expand=True)


class ExtractCache(Cache):

    """
    A redis cache of source_url => extracted data.
    """
    key_prefix = settings.EXTRACT_CACHE_PREFIX
    ttl = settings.EXTRACT_CACHE_TTL

    def work(self, url, type='article'):
        """
        Standardize + cache a raw url
        returning it's standardized url + global bitly url.
        """
        return article.extract(url, type=type)


class ThumbnailCache(Cache):

    """
    A redis cache of img url to base 64 thumbnail.
    """
    key_prefix = settings.THUMBNAIL_CACHE_PREFIX
    ttl = settings.THUMBNAIL_CACHE_TTL

    def work(self, img_url):
        """
        Grab an image and create a b64 encoded thumbnail.
        """
        return image.b64_thumbnail_from_url(img_url)
