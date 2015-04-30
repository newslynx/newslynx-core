"""
All things related to url parsing normalization.
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Most of the code here was extracted from newspaper's module for cleaning urls.
From: https://github.com/codelucas/newspaper/blob/master/newspaper/urls.py
"""

import copy
import time
import httplib
from urlparse import (
    urlparse, urljoin, urlsplit, urlunsplit, parse_qs
)
import logging

import requests
from requests import ConnectionError
import tldextract

from newslynx.core import bitly_api
from newslynx.lib import html
from newslynx.lib.regex import *

# suppress tld logging
tld_log = logging.getLogger('tldextract')
tld_log.setLevel(logging.CRITICAL)

# url chunks
ALLOWED_TYPES = [
    'html', 'htm', 'md', 'rst', 'aspx', 'jsp', 'rhtml', 'cgi',
    'xhtml', 'jhtml', 'asp'
]

GOOD_PATHS = [
    'story', 'article', 'feature', 'featured', 'slides',
    'slideshow', 'gallery', 'news', 'video', 'media',
    'v', 'radio', 'press', 'blog', 'movies', "project",
    'interactive', 'app'
]

BAD_CHUNKS = [
    'careers', 'contact', 'about', 'faq', 'terms', 'privacy',
    'advert', 'preferences', 'feedback', 'info', 'browse', 'howto',
    'account', 'subscribe', 'donate', 'shop', 'admin'
]

BAD_DOMAINS = [
    'amazon', 'doubleclick', 'twitter',
    'facebook'
]

# @network.retry(attempts=2)


def prepare(raw_url, source=None, keep_params=('id')):
    """
    Operations that unshorten a url, reconcile embeds,
    resolves redirects, strip parameters (with optional
    ones to keep), and then attempts to canonicalize the url 
    by checking the page source's metadata.

    All urls that enter `merlynne` are first treated with this function.
    """
    # check short urls
    if is_short_url(raw_url):
        url = unshorten(raw_url, attempts=2)

    # reconcile embeds:
    url = _reconcile_embed(raw_url)

    # check for redirects / non absolute urls
    if source:
        source_domain = urlparse(source).netloc
        url = urljoin(source, url)
        url = _redirect_back(url, source_domain)

    # try to first get the canonical url
    canonical = canonicalize(url)
    if canonical is not False:
        return canonical

    # remove arguments w/ optional parameters to keep.
    url = _remove_args(url, keep_params)

    # oh, well, lets just remove `index.html`
    # and call it a day.
    url = re_index_html.sub('', url)

    return url

# @network.retry(attempts=2)


def unshorten(short_url, **kw):

    # set vars
    pattern = kw.get('pattern', None)
    max_attempts = kw.get('max_attempts', 2)
    raise_err = kw.get('raise_err', False)
    interval = kw.get('interval', 1.5)
    factor = kw.get('factor', 2)
    success = False
    attempts = 0

    # absolutify url
    if not short_url.startswith('http://'):
        short_url = "http://" + short_url

    url = copy(short_url)

    # recursively unshorten
    while attempts < max_attempts:
        url = _unshorten(url, pattern=pattern)
        attempts += 1
        if not is_short_url(url, pattern=pattern) and _is_valid(url):
            success = True
            break
        interval *= factor
        time.sleep(interval)

    # if it's not a short_url return
    if success:
        return url

    # otherwise fallback to err / default return
    else:
        if raise_err:
            raise UnshortenError("Failed to unshorten: %s" % short_url)
        else:
            return short_url

def shorten(url):
    """
    Shorten a url on bitly, return it's new short url
    and global hash.
    """
    d = bitly_api.shorten(url)
    return {
        'short_url': d.get('url'),
        'global_hash': d.get('global_hash')
    }

def canonicalize(url):
    """
    Fetch the canonical url from a page.
    """
    canonical_url = False
    response = requests.get(url)

    if response.status_code == 200:
        soup = html.make_soup(response.text)
        canonical = soup.find("link", rel="canonical")

        if canonical:
            canonical_url = canonical['href']

        else:
            og_url = soup.find("meta", property="og:url")

            if og_url:
                canonical_url = og_url.get('content')

    return canonical_url


def get_domain(url, **kw):
    """
    Returns a url's domain, this method exists to
    encapsulate all url code into this file
    """
    if url is None:
        return None
    return urlparse(url, **kw).netloc


def get_simple_domain(url):
    """
    Returns a standardized domain
    i.e.:
    ``` 
    > get_simple_domain('http://publiceditor.blogs.nytimes.com/')
    > 'nytimes'
    ```
    """
    domain = get_domain(url)
    tld_dat = tldextract.extract(domain)
    return tld_dat.domain


def get_scheme(url, **kw):
    """
    returns a url's scheme, this method exists to
    encapsulate all url code into this file
    """
    if url is None:
        return None
    return urlparse(url, **kw).scheme


def get_path(url, **kw):
    """
    returns a url's path, this method exists to
    encapsulate all url code into this file
    """
    if url is None:
        return None
    return urlparse(url, **kw).path


def get_slug(url):
    """
    turn a url into a slug, removing (index).html 
    """
    url = get_path(url.decode('utf-8', 'ignore'))
    url = re_html.sub('', url).strip().lower()
    url = re_slug.sub(r'-', url)
    url = re_slug_end.sub('', url)

    if url.startswith('-'):
        url = url[1:]
    elif url.endswith('-'):
        url = url[-1]

    return url.strip()


def get_hash(url):
    """
    turn a url into a unique md5 hash
    """
    url = re_http.sub('', url)
    url = re_www.sub('', url)
    url = re_html.sub('', url).strip()
    return hashlib.md5(url).hexdigest()


def get_path_hash(url):
    """
    turn a url's path into a unique md5 hash
    """
    url = get_path(url)
    url = re_html.sub('', url)
    return hashlib.md5(url).hexdigest()


def get_filetype(url):
    """
    Input a URL and output the filetype of the file
    specified by the url. Returns None for no filetype.
    'http://blahblah/images/car.jpg' -> 'jpg'
    'http://yahoo.com'               -> None
    """
    path = urlparse(url).path
    # Eliminate the trailing '/', we are extracting the file
    if path.endswith('/'):
        path = path[:-1]
    path_chunks = [x for x in path.split('/') if len(x) > 0]
    last_chunk = path_chunks[-1].split('.')  # last chunk == file usually
    file_type = last_chunk[-1] if len(last_chunk) >= 2 else None
    return file_type or None


def is_article(url, pattern=None):
    """
    Check if a url looks like it's an article.
    First, perform a few basic checks like making sure the format of the url
    is right, (scheme, domain, tld).
    Second, make sure that the url isn't some static resource, check the
    file type.
    Then, search of a YYYY/MM/DD pattern in the url. News sites
    love to use this pattern, this is a very safe bet.
    Separators can be [\.-/_]. Years can be 2 or 4 digits, must
    have proper digits 1900-2099. Months and days can be
    ambiguous 2 digit numbers, one is even optional, some sites are
    liberal with their formatting also matches snippets of GET
    queries with keywords inside them. ex: asdf.php?topic_id=blahlbah
    We permit alphanumeric, _ and -.
    Our next check makes sure that a keyword is within one of the
    separators in a url (subdomain or early path separator).
    cnn.com/story/blah-blah-blah would pass due to "story".
    We filter out articles in this stage by aggressively checking to
    see if any resemblance of the source& domain's name or tld is
    present within the article title. If it is, that's bad. It must
    be a company link, like 'cnn is hiring new interns'.
    We also filter out articles with a subdomain or first degree path
    on a registered bad keyword.
    """

    # optionally apply regex
    if pattern:
        pattern = compile_regex(pattern)
        if pattern.match(url):
            return True

    # 11 chars is shortest valid url length, eg: http://x.co
    if url is None or len(url) < 11:
        return False

    r1 = ('mailto:' in url)  # TODO not sure if these rules are redundant
    r2 = ('http://' not in url) and ('https://' not in url)

    if r1 or r2:
        return False

    path = urlparse(url).path

    # input url is not in valid form (scheme, netloc, tld)
    if not path.startswith('/'):
        return False

    # the '/' which may exist at the end of the url provides us no information
    if path.endswith('/'):
        path = path[:-1]

    # '/story/cnn/blahblah/index.html' --> ['story', 'cnn', 'blahblah', 'index.html']
    path_chunks = [x for x in path.split('/') if len(x) > 0]

    # siphon out the file type. eg: .html, .htm, .md
    if len(path_chunks) > 0:
        file_type = get_filetype(url)

        # if the file type is a media type, reject instantly
        if file_type and file_type not in ALLOWED_TYPES:
            return False

        last_chunk = path_chunks[-1].split('.')
        # the file type is not of use to use anymore, remove from url
        if len(last_chunk) > 1:
            path_chunks[-1] = last_chunk[-2]

    # Index gives us no information
    if 'index' in path_chunks:
        path_chunks.remove('index')

    # extract the tld (top level domain)
    tld_dat = tldextract.extract(url)
    subd = tld_dat.subdomain
    tld = tld_dat.domain.lower()

    url_slug = path_chunks[-1] if path_chunks else u''

    if tld in BAD_DOMAINS:
        return False

    if len(path_chunks) == 0:
        dash_count, underscore_count = 0, 0
    else:
        dash_count = url_slug.count('-')
        underscore_count = url_slug.count('_')

    # If the url has a news slug title
    if url_slug and (dash_count > 4 or underscore_count > 4):

        if dash_count >= underscore_count:
            if tld not in [x.lower() for x in url_slug.split('-')]:
                return True

        if underscore_count > dash_count:
            if tld not in [x.lower() for x in url_slug.split('_')]:
                return True

    # There must be at least 2 subpaths
    if len(path_chunks) <= 1:
        return False

    # Check for subdomain & path red flags
    # Eg: http://cnn.com/careers.html or careers.cnn.com --> BAD
    for b in BAD_CHUNKS:
        if b in path_chunks or b == subd:
            return False

    match_date = re_url_date.search(url)

    # if we caught the verified date above, it's an article
    if match_date:
        return True

    for GOOD in GOOD_PATHS:
        if GOOD.lower() in [p.lower() for p in path_chunks]:
            return True

    return False

# SHORT DOMAINS #


def is_short_url(url, pattern=None):
    """
    test url for short links, allow str / list / retype's and passing in custom urls
    """
    # pass in specific regexes
    if pattern:
        pattern = compile_regex(pattern)
        # only return if we match the custom domain, never fail
        # because of this
        if pattern.match(url):
            return True

    # test against bitly-ish short url pattern
    if re_short_url.search(url):
        return True

    # test against known short domains
    domain = get_domain(url)
    if re_short_domains.search(domain):
        return True

    return False


def is_abs(url):
    """
    check if a url is absolute.
    """
    return re_abs_url.search(url.lower()) is not None


def from_string(string, dedupe=True):
    """
    get urls from input string
    """
    urls = re_url.findall(string)
    short_urls = [g[0] for g in re_short_url_text.findall(string)]
    final_urls = urls + short_urls
    if dedupe:
        return list(set(final_urls))
    else:
        return final_urls


def from_html(htmlstring, domain=None, dedupe=True):
    """
    Extract urls from htmlstring, optionally reconciling
    relative urls
    """
    final_urls = []

    soup = html.make_soup(htmlstring)

    for a in soup.find_all('a'):
        href = a.attrs.get('href', None)
        if href:
            if not is_abs(href):
                if domain:
                    href = prepare(urljoin(domain, href))

            final_urls.append(href)

    if dedupe:
        return list(set(final_urls))
    else:
        return final_urls


def _remove_args(url, keep_params=(), frags=False):
    """
    Remove all param arguments from a url.
    """
    parsed = urlsplit(url)
    filtered_query = '&'.join(
        qry_item for qry_item in parsed.query.split('&')
        if qry_item.startswith(keep_params)
    )
    if frags:
        frag = parsed[4:]
    else:
        frag = ('',)

    return urlunsplit(parsed[:3] + (filtered_query,) + frag)


def _redirect_back(url, source_domain=None):
    """
    Some sites like Pinterest have api's that cause news
    args to direct to their site with the real news url as a
    GET param. This method catches that and returns our param.
    """
    parse_data = urlparse(url)
    domain = parse_data.netloc
    query = parse_data.query

    # If our url is even from a remotely similar domain or
    # sub domain, we don't need to redirect.
    if source_domain in domain or domain in source_domain:
        return url

    query_item = parse_qs(query)
    if query_item.get('url'):
        return query_item['url'][0]

    return url


def _reconcile_embed(url):
    """
    make an embedded movie url like this:
    //www.youtube.com/embed/vYNnPx8fZBs
    into a full url
    """
    if url.startswith('//'):
        url = "http{}".format(url)
    return url


def _is_valid(url):
    """
    method just for checking weird results from `_get_location` in `_unshorten`
    """
    return len(url) > 11 and 'localhost' not in url


def _get_location(url):
    """
    most efficient yet error prone method for unshortening a url.
    """
    try:
        parsed = urlparse(url)
        h = httplib.HTTPConnection(parsed.netloc)
        h.request('HEAD', parsed.path)
        response = h.getresponse()
        if response.status / 100 == 3 and response.getheader('Location'):
            return response.getheader('Location')
        else:
            return url

    # DONT FAIL
    except:
        return url

def _long_url(url):
    """
    hit long url's api to unshorten a url
    """

    try:
        r = requests.get(
            'http://api.longurl.org/v2/expand',
            params={
                'url':  url,
                'format': 'json'
            }
        )

    except ConnectionError:
        return url

    else:
        if r.status_code == 200:
            return r.json().get('long-url', url)

    # DONT FAIL
    return url

def _bypass_bitly_warning(url):
    """
    Sometime bitly blocks unshorten attempts, this bypasses that.
    """
    r = requests.get(url)
    if r.status_code == 200:
        soup = html.make_soup(r.content)
        a = soup.find('a', {'id': 'clickthrough'})
        return a.attrs.get('href')

    return url


def _unshorten(url, pattern=None):
    """
    quad-method approach to unshortening a url
    """

    # method 1, get location
    url = _get_location(url)
    if not is_short_url(url, pattern=pattern):
        return url

    # check if there's a bitly warning.
    if re_bitly_warning.search(url):
        url = _bypass_bitly_warning(url)
        if not is_short_url(url, pattern=pattern):
            return url

    # method 2, use longurl.com
    url = _long_url(url)
    if not is_short_url(url, pattern=pattern):
        return url

    # method 3, use requests
    try:
        r = requests.get(url)
    except ConnectionError:
        return url
    else:
        if r.status_code == 200:
            url = r.url
            if not is_short_url(url, pattern=pattern):
                return url

    # return whatever we have
    return url
