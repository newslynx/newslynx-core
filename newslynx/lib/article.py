"""
Multi-Method Article Extraction
"""

import logging

from bs4 import BeautifulSoup

from newslynx.lib.common import make_soup
from newslynx.core import settings
from newslynx.lib import network
from newslynx.lib import url
from newslynx.lib import html
from newslynx.lib import meta
from newslynx.lib import author
from newslynx.lib import embed

try:
    from newslynx.core import embedly_api
except ImportError:
    pass

log = logging.getLogger(__name__)


def extract(source_url, **kw):
    """
    Article extraction. Method is as follows:
    1. Get html from url.
    2. Canonicalize URL.
    3. If not canonical, prepare the url.
    4. Extract meta tags.
    5. If embedly is active, use it for content extraction.
    6. If embedly doesnt return content or is not active, use readability
    7. If readability doesnt return content, use article tag.
    8. If authors aren't detcted from meta tags, detect them in article body.
    """
    type = kw.get('type', 'article')

    # fetch page
    page_html = network.get(source_url)

    # something failed.
    if not page_html:
        log.warning("Failed to extract html from {}".format(source_url))
        return None

    soup = make_soup(page_html)

    # get canonical url
    canonical_url = meta.canonical_url(soup)
    if not canonical_url:
        canonical_url = url.prepare(
            source_url, source=source_url, canonicalize=False)

    # domain
    domain = url.get_domain(canonical_url)

    # get meta tags + other data
    data = {
        'url': canonical_url,
        'domain': domain,
        'title': meta.title(soup, canonical_url),
        'description': meta.description(soup, canonical_url),
        'img_url': meta.img_url(soup, canonical_url),
        'created': meta.publish_date(soup, canonical_url),
        'favicon': meta.favicon(soup, canonical_url),
        'site_name': meta.site_name(soup, canonical_url),
        'authors': author.extract(soup),
        'type': type,
        'body': None
    }

    # embed videos
    if url.is_video(canonical_url):
        data['type'] = 'video'
        data['body'] = embed.video(canonical_url)
        return data

    # extract article body
    if data['type'] == 'article':
        if settings.EMBEDLY_ENABLED:
            data['body'] = body_via_embedly(canonical_url)
        if not data['body']:
            data['body'] = body_via_readability(page_html, canonical_url)

        # # extract body from article tag
        body, raw_html = body_via_article_tag(soup, canonical_url)

        # merge body
        if not data['body']:
            data['body'] = body

        # get creators from raw article html
        if not len(data['authors']) and raw_html:
            data['authors'] = author.extract(raw_html, tags=author.OPTIMISTIC_TAGS)

            # remove site name from authors
            if data.get('site_name'):
                data['authors'] = [
                    a.replace(data['site_name'].upper(), "").strip()
                    for a in data['authors']
                ]

        # get links from raw_html + content
        links = [u for u in url.from_any(data['body']) if source_url not in u]
        for u in url.from_any(raw_html, source=source_url):
            if u not in links and (u != source_url or not u.startswith(source_url)):
                links.append(u)

        # split out internal / external links / article links
        data['links'] = links

    return data


def body_via_embedly(source_url):
    """
    Use Embed.ly's API for content extraction.
    """

    # make request to embedly api
    e = embedly_api.extract(source_url)

    # check for errors.
    if e['type'] == 'error':
        return None

    return html.prepare(e.get('content'), source_url)


def body_via_readability(page_html, source_url):
    """
    Readbility is good at article + title.
    """
    from readability.readability import Document
    
    obj = Document(page_html)
    body = obj.summary()
    if not body:
        return None
    return html.prepare(body, source_url)


def body_via_article_tag(soup, source_url):
    """
    Extract content from an "article" tag.
    """
    if not isinstance(soup, BeautifulSoup):
        soup = make_soup(soup)
    articles = soup.find_all('article')
    if len(articles):
        raw_html = html.get_inner(articles[0])
        body = html.prepare(raw_html, source_url)
        return body, raw_html
    return None, None
