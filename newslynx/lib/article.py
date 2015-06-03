"""
Multi-Method Article Extraction
"""
import logging

from readability.readability import Document
from bs4 import BeautifulSoup

from newslynx import settings
from newslynx.lib import network
from newslynx.lib import url
from newslynx.lib import html
from newslynx.lib import meta
from newslynx.lib import author

log = logging.getLogger(__name__)


def extract(source_url):
    """
    Article extraction. Method is as follows:
    1. Get html from url.
    2. Canonicalize URL.
    3. If not canonical, prepare the url.
    4. Extract meta tags.
    5. If embedly is active, use it for content extraction.
    6. If embedly doesnt return content, use readability
    7. If readability doesnt return content, use meta tag.
    """

    # fetch page
    page_html = network.get_html(source_url)

    # something failed.
    if not page_html:
        log.warning("Failed to extract html from {}".format(source_url))
        return {}

    soup = BeautifulSoup(page_html)

    # get canonical url
    canonical_url = meta.canonical_url(soup)
    if not canonical_url:
        canonical_url = url.prepare(source_url, source=source_url, canonicalize=False)

    # get meta tags + other data
    data = {
        'url': canonical_url,
        'domain': url.get_domain(canonical_url),
        'title': meta.title(soup, canonical_url),
        'description': meta.description(soup, canonical_url),
        'img_url': meta.img_url(soup, canonical_url),
        'created': meta.publish_date(soup, canonical_url),
        'favicon': meta.favicon(soup, canonical_url),
        'site_name': meta.site_name(soup, canonical_url),
        'authors': author.extract(soup),
        'content': None
    }

    # extract content from embedly + readability
    if settings.EMBEDLY_ENABLED:
        data['content'] = content_via_embedly(canonical_url)

    if not data['content']:
        data['content'] = content_via_readability(page_html, canonical_url)

    # extract content from article tag
    content, raw_html = content_via_article_tag(soup, canonical_url)

    # merge content
    if not data['content']:
        data['content'] = content

    # get creators from raw article html
    if not len(data['authors']) and raw_html:
        data['authors'] = author.extract(raw_html, tags=author.OPTIMISTIC_TAGS)

    # add in short urls
    if settings.BITLY_ENABLED:
        pass
        # short_data = url.shorten(canonical_url)
        # if short_data:
            # data.update(short_data)
    return data


def content_via_embedly(source_url):
    """
    Use Embed.ly's API for content extraction.
    """
    from newslynx.core import embedly_api

    # make request to embedly api
    e = embedly_api.extract(source_url)

    # check for errors.
    if e['type'] == 'error':
        return None

    return html.prepare(e.get('content'), source_url)


def content_via_readability(page_html, source_url):
    """
    Readbility is good at article + title.
    """

    obj = Document(page_html)
    content = obj.summary()
    if not content:
        return None
    return html.prepare(content, source_url)


def content_via_article_tag(soup, source_url):
    """
    Extract content from an "article" tag.
    """
    if not isinstance(soup, BeautifulSoup):
        soup = BeautifulSoup(soup)
    articles = soup.find_all('article')
    if len(articles):
        raw_html = html.get_inner(articles[0])
        content = html.prepare(raw_html, source_url)
        return content, raw_html
    return None, None
