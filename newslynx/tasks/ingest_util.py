from gevent.monkey import patch_all
patch_all()
from gevent.pool import Pool

from newslynx.lib import dates
from newslynx.lib import url
from newslynx.lib import text
from newslynx.lib import html
from newslynx.models import URLCache
from newslynx import settings
from newslynx.exc import RequestError

# the url cache object
url_cache = URLCache()

# a pool to multithread url_cache.
url_cache_pool = Pool(settings.URL_CACHE_POOL_SIZE)


def extract_urls(obj, fields, source=None, links=[]):
    """
    Extract, normalize, and dedupe urls from
    text/html fields in an object.
    """
    raw_urls = set(links)
    for f in fields:
        v = obj.get(f)
        if v:
            for u in url.from_any(str(v), source=source):
                raw_urls.add(u)

    clean_urls = set()
    for cache_response in url_cache_pool.imap_unordered(url_cache.get, list(raw_urls)):
        clean_urls.add(cache_response.value)
    return list(clean_urls)


def prepare_str(o, field, source_url=None):
    """
    Prepare text/html field
    """
    if field not in o:
        return None
    if o[field] is None:
        return None
    if html.is_html(o[field]):
        return html.prepare(o[field], source_url)
    return text.prepare(o[field])


def prepare_date(o, field):
    """
    Prepare a date
    """
    if field not in o:
        return None
    if o[field] is None:
        return None
    dt = dates.parse_any(o[field])
    if not dt:
        raise RequestError(
            '{}: {} is an invalid date.'
            .format(field, o[field]))
    return dt


def prepare_url(o, field):
    """
    Prepare a url
    """
    if field not in o:
        return None
    if o[field] is None:
        return None
    cache_response = url_cache.get(o[field])
    return cache_response.value


def check_requires(o, requires, type='Event'):
    """
    Check for presence of required fields.
    """
    # check required fields
    for k in requires:
        if k not in o:
            raise RequestError(
                "Missing '{}'. An {} Requires {}"
                .format(k, type, requires))


def split_meta(obj, cols):
    """
    Split out meta fields from core columns.
    """
    meta = obj.pop('meta', {})
    for k in obj.keys():
        if k not in cols:
            meta[k] = obj.pop(k)
    obj['meta'] = meta
    return obj
