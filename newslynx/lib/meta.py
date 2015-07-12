"""
All things related to metadata parsing
"""

from urlparse import urlparse
from urlparse import urljoin

import tldextract

from newslynx.lib.regex import re_url_date
from newslynx.lib import dates
from newslynx.lib import text

# KNOWN META TAGS FOR KEY DATA ATTRIBUTES ORDERED BY PREFERENCE

CANONICAL_URL_TAGS = [
    {'tag': 'link', 'attr': 'rel', 'val': 'canonical', 'data': 'href'},
    {'tag': 'meta', 'attr': 'property', 'val': 'og:url', 'data': 'content'},
    {'tag': 'meta', 'attr': 'property', 'val': 'twitter:url', 'data': 'content'},
    {'tag': 'meta', 'attr': 'name', 'val': 'canonicalURL', 'data': 'content'},
    {'tag': 'meta', 'attr': 'name', 'val': 'original-source', 'data': 'content'},
    {'tag': 'meta', 'attr': 'name', 'val': 'parsely-link', 'data': 'content'}
]

TITLE_TAGS = [
    {'tag': 'meta', 'attr': 'property', 'val': 'og:title', 'data': 'content'},
    {'tag': 'meta', 'attr': 'property', 'val': 'twitter:title', 'data': 'content'},
    {'tag': 'meta', 'attr': 'name', 'val': 'parsely-title', 'data': 'content'}
]

DESC_TAGS = [
    {'tag': 'meta', 'attr': 'property', 'val': 'og:description', 'data': 'content'},
    {'tag': 'meta', 'attr': 'property', 'val': 'twitter:description', 'data': 'content'},
    {'tag': 'meta', 'attr': 'itemprop', 'val': 'description', 'data': 'content'},
    {'tag': 'meta', 'attr': 'name', 'val': 'description', 'data': 'content'}
]

SITE_NAME_TAGS = [
    {'tag': 'meta', 'attr': 'property', 'val': 'og:site_name', 'data': 'content'},
    {'tag': 'meta', 'attr': 'property', 'val': 'twitter:site', 'data': 'content'},
    {'tag': 'meta', 'attr': 'name', 'val': 'parsely-type', 'data': 'content'}
]

PAGE_TYPE_TAGS = [
    {'tag': 'meta', 'attr': 'property', 'val': 'og:type', 'data': 'content'}
]

IMG_TAGS = [
    {'tag': 'meta', 'attr': 'property', 'val': 'og:image', 'data': 'content'},
    {'tag': 'meta', 'attr': 'property', 'val': 'twitter:image', 'data': 'content'},
    {'tag': 'meta', 'attr': 'property', 'val': 'twitter:image:src', 'data': 'content'},
    {'tag': 'meta', 'attr': 'itemprop', 'val': 'image', 'data': 'content'},
    {'tag': 'meta', 'attr': 'name', 'val': 'og:image', 'data': 'content'},
    {'tag': 'meta', 'attr': 'name', 'val': 'twitter:image', 'data': 'content'},
    {'tag': 'meta', 'attr': 'name', 'val': 'twitter:image:src', 'data': 'content'},
    {'tag': 'meta', 'attr': 'name', 'val': 'image', 'data': 'content'},
]

FAVICON_TAGS = [
    {'tag': 'link', 'attr': 'rel', 'val': 'icon', 'data': 'href'},
    {'tag': 'link', 'attr': 'rel', 'val': 'shortcut icon', 'data': 'href'},
]

PUBLISH_DATE_TAGS = [
    {'tag': 'meta', 'attr': 'property', 'val': 'article:published_time', 'data': ['content', 'datetime', 'date']},
    {'tag': 'meta', 'attr': 'name', 'val': 'article:published_time', 'data': ['content', 'datetime', 'date']},
    {'tag': 'meta', 'attr': 'property', 'val': 'rnews:datePublished', 'data': ['content', 'datetime', 'date']},
    {'tag': 'meta', 'attr': 'name', 'val': 'OriginalPublicationDate', 'data': ['content', 'datetime', 'date']},
    {'tag': 'meta', 'attr': 'itemprop', 'val': 'datePublished', 'data': ['content', 'datetime', 'date']},
    {'tag': 'meta', 'attr': 'property', 'val': 'og:published_time', 'data': ['content', 'datetime', 'date']},
    {'tag': 'meta', 'attr': 'name', 'val': 'article_date_original', 'data': ['content', 'datetime', 'date']},
    {'tag': 'meta', 'attr': 'name', 'val': 'publication_date', 'data': ['content', 'datetime', 'date']},
    {'tag': 'meta', 'attr': 'name', 'val': 'sailthru.date', 'data': ['content', 'datetime', 'date']},
    {'tag': 'meta', 'attr': 'name', 'val': 'PublishDate', 'data': ['content', 'datetime', 'date']},
    {'tag': 'meta', 'attr': 'property', 'val': 'article:published', 'data': ['content', 'datetime', 'date']},
    {'tag': 'meta', 'attr': 'name', 'val': 'parsely-pub-date', 'data': 'content'}
]


def canonical_url(soup, source_url=None):
    """
    Fetch the canonical url from meta fields.
    """
    for tag in CANONICAL_URL_TAGS:
        data = _extract_tag_data(soup, tag)
        if data:
            if source_url and data.startswith('/'):
                return urljoin(source_url, data)
            return data


def title(soup, source_url=None):
    """
    Extract meta title.
    """
    for tag in TITLE_TAGS:
        data = _extract_tag_data(soup, tag)
        if data:
            return text.prepare(data)

    # fallback on page title
    if soup.title:
        return text.prepare(soup.title.text.strip())


def description(soup, source_url=None):
    """
    Extract meta description.
    """
    for tag in DESC_TAGS:
        data = _extract_tag_data(soup, tag)
        if data:
            return text.prepare(data)


def site_name(soup, source_url=None):
    """
    Extract site name from meta.
    """
    for tag in SITE_NAME_TAGS:
        data = _extract_tag_data(soup, tag)
        if data:
            # handle twitter site which is actually
            # twitter username.
            if not data.startswith('@'):
                return data

    # fallback to extracting and title casing simplified domain
    if source_url:
        domain = urlparse(source_url).netloc
        if domain:
            tld_dat = tldextract.extract(domain)
            return tld_dat.domain.replace('.', ' ').strip().title()


def page_type(soup, source_url=None):
    """
    Returns meta type of a page, open graph protocol
    """
    for tag in PAGE_TYPE_TAGS:
        data = _extract_tag_data(soup, tag)
        if data:
            return data


def img_url(soup, source_url=None):
    """
    Extract meta image url.
    """
    for tag in IMG_TAGS:
        data = _extract_tag_data(soup, tag)
        if data:
            if data.startswith('//'):
                data = 'http' + data
            return data


def publish_date(soup, source_url=None):
    """
    Extract publish date from meta / source_url.
    """

    # try isodate first
    for tag in PUBLISH_DATE_TAGS:
        ds = _extract_tag_data(soup, tag)
        if ds:
            dt = dates.parse_iso(ds, enforce_tz=False)
            if dt:
                return dt

    # try a timestamp next.
    for tag in PUBLISH_DATE_TAGS:
        ds = _extract_tag_data(soup, tag)
        if ds:
            dt = dates.parse_ts(ds)
            if dt:
                return dt

    # try any date next.
    for tag in PUBLISH_DATE_TAGS:
        ds = _extract_tag_data(soup, tag)
        if ds:
            dt = dates.parse_any(ds, enforce_tz=False)
            if dt:
                return dt

    # fallback on url regex
    if source_url:
        dm = re_url_date.search(source_url)
        if dm:
            ds = dm.group(0)
            dt = dates.parse_any(ds, enforce_tz=False)
            if dt:
                return dt


def favicon(soup, source_url=None):
    """
    Extract favicon from meta / logic.
    """
    for tag in FAVICON_TAGS:
        data = _extract_tag_data(soup, tag)
        if data:
            if not data.startswith('/'):
                return data

    # fallback on usual location.
    if source_url:
        parsed_uri = urlparse(source_url)
        domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return domain + 'favicon.ico'


def _extract_tag_data(soup, tag):
    """
    Extract data from tag
    """
    # otherwise search more thoroughly
    attr_dict = {tag['attr']: tag['val']}
    el = soup.find(tag['tag'], attr_dict)
    if el:
        if not isinstance(tag['data'], list):
            tag['data'] = [tag['data']]
        for v in tag['data']:
            data = el.get(v)
            if data:
                return data
