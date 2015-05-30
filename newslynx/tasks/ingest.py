from gevent.pool import Pool

from newslynx.lib import url
from newslynx.models import url_cache, Event, Thing
from newslynx.exc import RequestError
from newslynx.models.util import split_meta, get_table_columns


# a pool to multithread url_cache.
url_extract_pool = Pool(settings.URL_CACHE_POOL_SIZE)


def extract_urls(obj, fields):
    """
    Extract and normalize urls from text/html fields in an object.
    """
    urls = set()
    for f in fields:
        v = obj.get(f)
        if v:
            for u in url.from_html(v):
                if u not in urls:
                    urls.add(u)
                    yield u

            for u in url.from_string(v):
                if u not in urls:
                    urls.add(u)
                    yield u


def event(raw_obj,
          url_fields=['title', 'text', 'description'],
          requires=['source_id', 'org_id', 'url', 'title', 'text']):

        # get event columns.
    cols = [c for c in get_table_columns(Event) if c != 'meta']

    # check required fields
    for k in requires:
        if k not in raw_obj:
            raise RequestError(
                "Missing '{}'. An Event Requires {}".format(k, requires))

    # split out meta fields
    raw_obj = split_meta(raw_obj, cols)

    # extract urls in pool
    raw_urls = extract_urls(raw_obj, fields=url_fields)
    clean_urls = []

    for u in url_extract_pool.imap_unordered(url_cache.get, raw_urls):
        clean_urls.append(u)

    # Detect Things
    if len(clean_urls):
        pass

        
