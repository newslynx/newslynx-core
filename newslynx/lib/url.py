"""
All things related to url parsing.

Most of the code here was modified from newspaper's module for cleaning urls.
From: https://github.com/codelucas/newspaper/blob/master/newspaper/urls.py
"""

import copy
import time
from urlparse import (
    urlparse, urljoin, urlsplit, urlunsplit, parse_qs
)

import tldextract

from newslynx.lib.common import make_soup
from newslynx.lib import network
from newslynx.lib import meta
from newslynx.lib import html
from newslynx.util import uniq
from newslynx.core import settings
from newslynx.lib.regex import *

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
    'account', 'subscribe', 'donate', 'shop', 'admin', 'author', 'topic',
    'comments'
]

BAD_DOMAINS = [
    'amazon', 'doubleclick', 'twitter',
    'facebook', 'pinterest', 'google',
]

VIDEO_DOMAINS = [
    'youtube', 'vimeo', 'dailymotion', 'kewego'
]

URL_TAGS = ['a', 'embed', 'video', 'iframe']

URL_ATTRS = ['href', 'src']

MAX_LEN = 150
MIN_LEN = 11

IMG_FILETYPES = frozenset([
    'png', 'jpg', 'jpeg', 'gif',
    'bmp', 'webp', 'tiff', 'svg', 'ico'
])

REDIRECT_QUERY_PARAMS = ['url', 'u']

KEEP_PARAMS = ('id', 'p', 'v', 'story_fbid')


def prepare(url, source=None, canonicalize=True, expand=True, keep_params=KEEP_PARAMS):
    """
    Operations that unshorten a url, reconcile embeds,
    resolves redirects, strip parameters (with optional
    ones to keep), and then attempts to canonicalize the url
    by checking the page source's metadata.

    All urls that enter `merlynne` are first treated with this function.
    """
    if not url or url == "":
        return None

    # encode.
    url = url.encode('utf-8', errors='ignore')

    # reconcile embeds:
    url = reconcile_embed(url)

    # reconcile redirects
    url = redirect_back(url, source)

    # check for non absolute urls.
    if source:
        source_domain = get_domain(source)

        # if the domain is in the source, attempt to absolutify it
        if source_domain in url:

            # check for non-absolute urls
            if not is_abs(url):
                url = urljoin(source, url)

    # check for missing scheme
    if not get_scheme(url):
        url = "http://{}".format(url)

    # check short urls
    if expand:
        if is_shortened(url):
            url = unshorten(url, attempts=1)

    # canonicalize
    if canonicalize:
        page_html = network.get(url)
        if page_html:
            soup = make_soup(page_html)
            _url = meta.canonical_url(soup)
            if _url:
                url = _url

    # if it got converted to None, return
    if not url:
        return None

    # remove arguments w/ optional parameters to keep.
    url = remove_args(url, keep_params)

    # remove index.html
    url = re_index_html.sub('', url)

    # always remove trailing slash
    if url.endswith('/'):
        url = url[:-1]
    return url


def join(base, path):
    """
    Join two url elements.
    """
    return urljoin(prepare(base, canonicalize=False, expand=False), path)


def unshorten(orig_url, **kw):
    """
    Unshorten a url.
    """
    if not orig_url:
        return None
    # set vars
    max_attempts = kw.get('max_attempts', 3)
    interval = kw.get('interval', 0.5)
    factor = kw.get('factor', 2)
    attempts = 0

    if not orig_url.startswith('http://'):
        orig_url = "http://" + orig_url
    u = copy.copy(orig_url)
    while attempts < max_attempts:
        u = _unshorten(u)
        attempts += 1
        # catch failures
        if not u:
            return orig_url
        # urls that probably aren't shortened.
        elif u == orig_url:
            return orig_url
        elif not is_shortened(u):
            return u
        interval *= factor
        time.sleep(interval)

    return u


@network.retry(attempts=settings.NETWORK_MAX_RETRIES)
def shorten(url):
    """
    Shorten a url on bitly, return it's new short url
    and global hash.
    """
    from newslynx.core import bitly_api
    d = bitly_api.shorten(url)
    return {
        'short_url': d.get('url'),
        'global_hash': d.get('global_hash')
    }


def get_domain(url, **kw):
    """
    Returns a url's domain, this method exists to
    encapsulate all url code into this file
    """
    if url is None:
        return None

    # check for missing scheme
    if not get_scheme(url):
        url = "http://{}".format(url)

    domain = urlparse(url, **kw).netloc
    domain = re_www.sub('', domain)
    return domain


def get_simple_domain(url, **kw):
    """
    Returns a standardized domain
    i.e.:
    get_simple_domain('http://publiceditor.blogs.nytimes.com/')
    >>> 'nytimes'
    """
    if url is None:
        return None
    domain = get_domain(url)
    tld_dat = tldextract.extract(domain, **kw)
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

    # check for missing scheme
    if not get_scheme(url):
        url = "http://{}".format(url)

    return urlparse(url, **kw).path


def get_slug(url):
    """
    turn a url into a slug, removing (index).html
    """
    if url is None:
        return None

    # check for missing scheme
    if not get_scheme(url):
        url = "http://{}".format(url)

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
    if url is None:
        return None

    # check for missing scheme
    if not get_scheme(url):
        url = "http://{}".format(url)

    url = re_http.sub('', url)
    url = re_www.sub('', url)
    url = re_html.sub('', url).strip()
    return hashlib.md5(url).hexdigest()


def get_path_hash(url, **kw):
    """
    turn a url's path into a unique md5 hash
    """
    if url is None:
        return None

    # check for missing scheme
    if not get_scheme(url):
        url = "http://{}".format(url)

    url = get_path(url, **kw)
    url = re_html.sub('', url)
    return hashlib.md5(url).hexdigest()


def get_query_string(url, **kw):
    """
    Get the query string from a url.
    """
    if url is None:
        return None

    # check for missing scheme
    if not get_scheme(url):
        url = "http://{}".format(url)

    return urlparse(url, **kw).query


def get_filetype(url, **kw):
    """
    Input a URL and output the filetype of the file
    specified by the url. Returns None for no filetype.
    'http://blahblah/images/car.jpg' -> 'jpg'
    'http://yahoo.com'               -> None
    """
    if url is None:
        return None

    # check for missing scheme
    if not get_scheme(url):
        url = "http://{}".format(url)

    path = get_path(url, **kw)
    # Eliminate the trailing '/', we are extracting the file
    if path.endswith('/'):
        path = path[:-1]
    path_chunks = [x for x in path.split('/') if len(x) > 0]
    if not len(path_chunks):
        return None
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
    if not path:
        return None

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


def is_video(url):
    """
    A really stupid test for whether a url is a video.
    """
    domain = get_domain(url)
    if not domain:
        return False
    for video_domain in VIDEO_DOMAINS:
        if video_domain in domain:
            return True
    return False


def is_internal(url, source_domain):
    """
    determine interal vs. external urls.
    """
    link_domain = get_domain(url)
    if source_domain in link_domain or link_domain in source_domain:
        return True
    return False


def is_image(url):
    """
    determine if a url is an image.
    """
    ext = get_filetype(url)
    if not ext:
        return False
    return ext in IMG_FILETYPES


# SHORT DOMAINS #

def is_shortened(url, pattern=None):
    """
    test url for short links.
    """
    # pass in specific regexes
    if pattern:
        pattern = compile_regex(pattern)
        # only return if we match the custom domain, never fail
        # because of this
        if pattern.match(url):
            return True

    # test against known short domains
    domain = get_domain(url)
    if re_short_domains.search(domain):
        return True

    # test against bitly-ish short url pattern
    if re_short_url.search(url):
        return True

    return False


def is_abs(url):
    """
    check if a url is absolute.
    """
    return bool(get_domain(url))


def from_string(string, **kw):
    """
    get urls from input string
    """

    source = kw.get('source', None)
    exclude_images = kw.get('excl_img', True)

    if not string:
        return []

    raw_urls = re_url.findall(string)
    short_urls = [g[0].strip() for g in re_short_url_text.findall(string) if g]

    urls = []
    if source:
        for url in raw_urls:
            if not is_abs(url):
                url = urljoin(source, url)
            urls.append(url)
    else:
        urls = [u for u in raw_urls if is_valid(u)]

    # make sure short url regex doesn't create partial dupes.
    for u in short_urls:
        if any([r.startswith(u) or u == r for r in urls]):
            short_urls.remove(u)

    # combine
    urls += short_urls

    # remove images.
    if exclude_images:
        urls = [u for u in urls if not is_image(u)]

    # remove invalid urls
    urls = [u for u in urls if is_valid(u)]

    return uniq(urls)


def from_html(htmlstring, **kw):
    """
    Extract urls from htmlstring, optionally reconciling
    relative urls + embeds + redirects.
    """
    source = kw.get('source', None)
    exclude_images = kw.get('excl_img', True)

    if not htmlstring:
        return []
    final_urls = []
    if source:
        source_domain = get_domain(source)
    soup = make_soup(htmlstring)
    for tag in URL_TAGS:

        for el in soup.find_all(tag):

            for attr in URL_ATTRS:
                href = el.attrs.get(attr, None)

                if not href:
                    continue
                url = reconcile_embed(href)

                if source:
                    url = redirect_back(url, source_domain)
                    if not is_abs(url):
                        url = urljoin(source, url)

                if not is_valid(url):
                    continue
                if exclude_images:
                    if not is_image(url):
                        final_urls.append(url)
                else:
                    final_urls.append(url)
    return uniq(final_urls)


def from_any(html_or_string, **kw):
    """
    Parse urls out of html or raw string.
    """
    if not html_or_string:
        return []
    if html.is_html(html_or_string):
        return from_html(html_or_string, **kw)
    return from_string(html_or_string, **kw)


def remove_args(url, keep_params, frags=False):
    """
    Remove all param arguments from a url.
    """
    if not url:
        return None
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


def redirect_back(url, source=None):
    """
    Some sites like Pinterest have api's that cause news
    args to direct to their site with the real news url as a
    GET param. This method catches that and returns our param.
    """
    domain = get_domain(url)
    query = get_query_string(url)

    if source:
        source_domain = get_domain(source)
        # If our url is even from a remotely similar domain or
        # sub domain, we don't need to redirect.
        if source_domain in domain or domain in source_domain:
            return url

    query_item = parse_qs(query)

    for k in REDIRECT_QUERY_PARAMS:
        if query_item.get(k):
            return query_item[k][0]
    return url


def get_query_param(url, param):
    """
    Get the value of a query parameter
    from a url.
    """
    p = urlparse(url)
    query_items = parse_qs(p.query)
    v = query_items.get(param)
    if not v or not len(v):
        return None
    return v[0]


def add_query_params(url, **kw):
    """
    Add/update query strings to a url.
    """
    p = urlparse(url)
    endpoint = "{}://{}{}".format(p.scheme, p.netloc, p.path)

    # allow for multiple query strings
    qs = [(k, v) for k, vv in parse_qs(p.query).items() for v in vv]

    # add in new query strings
    for k, v in kw.items():
        qs.append((k, str(v)))

    # format string
    qs = "&".join(["{}={}".format(q[0], q[1]) for q in qs])

    return "{}?{}".format(endpoint, qs)


def reconcile_embed(url):
    """
    make an embedded movie url like this:
    //www.youtube.com/embed/vYNnPx8fZBs
    into a full url
    """
    if not url:
        return None
    if url.startswith('//'):
        url = "http:{}".format(url)
    return url


def is_valid(url):
    """
    method just for checking weird results from `_get_location` in `_unshorten`
    """
    return MIN_LEN < len(url) < MAX_LEN and 'localhost' not in url and 'mailto:' not in url


def validate(url):
    """
    Check if a url is valid (for form inputs).
    """
    if not url:
        return False
    if re_url.search(url) is None:
        return False
    return is_valid(url)


def categorize_links(links, source_domain):
    """
    Take in a list of links and categorize them into
    internal / external / articles / videos
    """
    data = {
        'external': [],
        'internal': [],
        'articles': {
            'external': [],
            'internal': [],
        },
        'videos': [],
        'shortened': []
    }

    for l in links:

        # check it it's internal / external
        internal = is_internal(l, source_domain)

        # is it shortened
        if is_shortened(l):
            data['shortened'].append(l)

        # is it an article
        elif is_article(l):
            if internal:
                data['articles']['internal'].append(l)
            else:
                data['articles']['external'].append(l)

        # is it a video
        elif is_video(l):
            data['videos'].append(l)

        # fallback on internal / external.
        elif internal:
            data['internal'].append(l)
        else:
            data['external'].append(l)

    return data


# def _long_url(url):
#     """
#     hit long url's api to unshorten a url
#     """

#     r = requests.get(
#         'http://api.longurl.org/v2/expand',
#         params={
#             'url':  url,
#             'format': 'json'
#         }
#     )

#     if r.status_code == 200:
#         return r.json().get('long-url', url)

#     # DONT FAIL
#     return url


def _bypass_bitly_warning(url):
    """
    Sometime bitly blocks unshorten attempts, this bypasses that.
    """
    html_string = network.get(url)
    soup = make_soup(html_string)
    a = soup.find('a', {'id': 'clickthrough'})
    if a:
        return a.attrs.get('href')
    return url


@network.retry(attempts=1)
def _unshorten(url, pattern=None):
    """
    dual-method approach to unshortening a url
    """
    orig_url = copy.copy(url)

    # method 1, get location
    url = network.get_location(url)

    if not is_valid(url):
        return None

    # check if there's a bitly warning.
    if re_bitly_warning.search(url):
        url = _bypass_bitly_warning(url)
        if not is_shortened(url, pattern=pattern):
            return url

    return url
