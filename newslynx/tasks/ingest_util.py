from gevent.monkey import patch_all
patch_all()
from gevent.pool import Pool

from newslynx.lib import dates
from newslynx.lib import url
from newslynx.lib import text
from newslynx.lib import html
from newslynx.lib import stats
from newslynx.models import URLCache, ThumbnailCache
from newslynx import settings
from newslynx.exc import RequestError
from newslynx.constants import METRIC_FACET_KEYS

# the url cache object
url_cache = URLCache()
thumbnail_cache = ThumbnailCache()

# a pool to multithread url_cache.
url_cache_pool = Pool(settings.URL_CACHE_POOL_SIZE)


def prepare_links(links=[], domains=[]):
    """
    Prepare links to be tested against content items.
    """
    if len(domains):
        _links = []
        for l in links:
            if any([d in l for d in domains]):
                _links.append(l)
        links = _links
    raw_urls = list(set(links))
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
    dt = dates.parse_iso(o[field])
    if not dt:
        raise RequestError(
            '{}: {} is an invalid date.'
            .format(field, o[field]))
    return dt


def prepare_url(o, field, source=None):
    """
    Prepare a url
    """
    if field not in o:
        return None
    if o[field] is None:
        return None
    # prepare it first before the sending to the canoncilation cache
    u = url.prepare(o[field], source=source, canonicalize=False, expand=False)
    cache_response = url_cache.get(u)
    return cache_response.value


def prepare_thumbnail(o, field):
    """
    Prepare a url
    """
    if field not in o:
        return None
    if o[field] is None:
        return None
    u = o[field]

    # create a thumbnail from an image.
    cache_response = thumbnail_cache.get(u)
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


def prepare_metrics(
        obj,
        org_metric_lookup,
        valid_levels=[],
        parent_obj='ContentItem',
        check_timeseries=True
        ):
    """
    Validate a metric.
    """
    # check if metrics exist and are properly formatted.
    obj.update(obj.pop('metrics', {}))
    for k in obj.keys():
        m = org_metric_lookup.get(k)
        if not m:
            raise RequestError(
                "Metric '{}' does not exist at this level."
                .format(k))

        if m['faceted'] and not isinstance(obj[k], list):
            raise RequestError(
                "Metric '{}' is faceted but was not passed in as a list."
                .format(k))

        if m['faceted'] and not set(obj[k][0].keys()) == set(METRIC_FACET_KEYS):
            raise RequestError(
                "Metric '{}' is faceted, but it\'s elements are not properly formatted. "
                "Each facet must be a dictionary of '{\"facet\":\"facet_name\", \"value\": 1234}"
                .format(k))

        # parse number
        obj[k] = stats.parse_number(obj[k])
    return obj
