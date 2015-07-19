"""
All things related to rss parsing.  We make use of feedparser which
we manage within this repository => newslynx/lib/pkg/feedparser.py
"""

from gevent.monkey import patch_all
patch_all()
from gevent.pool import Pool

from copy import copy

import jsonpath_rw as jsonpath

from newslynx.lib.pkg import feedparser
from newslynx.lib import dates
from newslynx.lib import author
from newslynx.lib import html
from newslynx.lib import url
from newslynx.lib import article
from newslynx.lib import image
from newslynx.util import uniq
from newslynx.exc import RequestError

# JSONPATH CANDIDATES
URL_CANDIDATE_JSONPATH = [
    'id', 'feedburner_origlink', 'link', 'link[*].href'
]

# applies to feed AND individual entries.
DATE_CANDIDATE_JSONPATH = [
    'updated_parsed', 'published_parse'
]

AUTHOR_CANDIDATE_JSONPATH = [
    'author', 'author_detail.name', 'authors[*].name'
]

IMG_CANDIDATE_JSONPATH = [
    'media_content[*].url'
]

BODY_CANDIDATE_JSONPATH = [
    'content[*].value', 'content_detail.value'
]

TITLE_CANDIDATE_JSONPATH = [
    'title', 'title_detail.value'
]

DESCRIPTION_CANDIDATE_JSONPATH = [
    'summary_detail.value', 'summary'
]

TAG_CANDIDATE_JSONPATH = [
    'tags[*].label', 'tags[*].term'
]


def get_entries(feed_url, domains=[]):
    """
    Parser entries from an rss feed.
    """
    f = FeedExtractor(feed_url, domains)
    parsed = False
    for entry in f.run():
        parsed = True
        yield entry
    if not parsed:
        raise RequestError('No entries found for {}'.format(feed_url))


def extract_entries(feed_url, domains=[]):
    """
    Parse entries from an rss feed and run article extraction
    an each
    """
    entries = get_entries(feed_url, domains)
    urls = [e['url'] for e in entries if e.get('url')]
    p = Pool(len(urls))
    for i, a in enumerate(p.imap_unordered(article.extract, urls)):
        yield a


def extract_articles(feed_url, domains=[]):
    """
    Parse entries from an rss feed, extract article urls, and
    run article extraction an each
    """
    entries = FeedExtractor(feed_url, domains).run()
    urls = [e['url'] for e in entries if url.is_article(e.get('url'))]
    p = Pool(len(entries))
    for i, a in enumerate(p.imap_unordered(article.extract, urls)):
        yield a


class FeedExtractor(object):

    def __init__(self, feed_url, domains):
        self.feed_url = feed_url
        self.domains = domains

    def get_jsonpath(self, obj, path, null=[]):
        """
        from https://pypi.python.org/pypi/jsonpath-rw/1.3.0
        parse a dict with jsonpath:
        usage:
        d = {'a' : [{'a':'b'}]}
        get_jsonpath(d, 'a[0].a')
        ['b']
        """
        jp = jsonpath.parse(path)
        res = [m.value for m in jp.find(obj)]
        if len(res) == 0:
            return null
        return res

    def get_candidates(self, obj, jsonpaths):
        """
        evaluate an object with jsonpaths,
        and get all unique vals / lists
        of values
        """
        candidates = []
        for path in jsonpaths:
            path_candidates = self.get_jsonpath(obj, path)

            if isinstance(path_candidates, list):
                for candidate in path_candidates:
                    if candidate:
                        candidates.append(candidate)

            elif isinstance(path_candidates, str):
                candidates.append(candidate)

        return uniq(candidates)

    def pick_longest(self, candidates):
        """
        Pick the longest option of all candidates
        """
        if len(candidates) == 0:
            return None
        candidates.sort(key=len)
        return candidates[-1]

    def get_created(self, obj):
        """
        return earliest time of candidates or current time.
        """
        candidates = self.get_candidates(obj, DATE_CANDIDATE_JSONPATH)
        if len(candidates) > 0:
            return dates.from_struct_time(sorted(candidates)[0])
        else:
            return dates.now()

    # get title
    def get_title(self, entry):
        """
        return all candidates, and parse unique
        """
        titles = self.get_candidates(entry, TITLE_CANDIDATE_JSONPATH)
        return self.pick_longest(titles)

    # get title
    def get_description(self, entry):
        """
        return all candidates, and parse unique
        """
        descriptions = self.get_candidates(
            entry, DESCRIPTION_CANDIDATE_JSONPATH)
        return self.pick_longest(descriptions)

    # get authors
    def get_authors(self, entry):
        """
        return all candidates, and parse unique
        """
        authors = []
        candidates = self.get_candidates(entry, AUTHOR_CANDIDATE_JSONPATH)
        for c in candidates:
            for a in author.parse(c):
                authors.append(a)
        return uniq(authors)

    # get images
    def get_img_url(self, entry, body):
        """
        Get the top image url.
        """
        img_urls = self.get_candidates(entry, IMG_CANDIDATE_JSONPATH)
        if len(img_urls):
            return img_urls[0]
        img_urls = image.from_html(body)

        if len(self.domains):
            for u in img_urls:
                if any([d in u for d in self.domains]):
                    return u

        # gifs are usually tracking pixels
        img_urls = [i for i in img_urls if not i.endswith('gif')]

        if len(img_urls):
            return img_urls[0]

    def get_body(self, entry):
        """
        Get all body candidates and check which one is the longest.
        """
        candidates = self.get_candidates(entry, BODY_CANDIDATE_JSONPATH)
        return self.pick_longest(candidates)

    def get_tags(self, entry):
        """
        Get all tags.
        """
        tags = self.get_candidates(entry, TAG_CANDIDATE_JSONPATH)
        return uniq([t.upper() for t in tags if t and t.strip() != ""])

    def get_url(self, entry):
        """
        Get the url.
        """
        # get potential candidates
        candidates = self.get_candidates(entry, URL_CANDIDATE_JSONPATH)

        # if no candidates, return an empty string
        if len(candidates) == 0:
            return None

        # test for urls in domains.
        if len(self.domains):
            urls = []
            for u in candidates:
                if u and any([d in u for d in self.domains if d]):
                    urls.append(u)
        else:
            urls = copy(candidates)

        # if we have one or more, update return the first.
        urls = list(urls)
        urls.sort(key=len)
        if len(urls) >= 1:
            return urls[-1]

        # if we STILL haven't found anything, just
        # return the first candidate that looks like a url.
        return [u for u in candidates if u.startswith('http')][0]

    def get_links(self, body, entry_url):
        """
        Extract links in the article body.
        """
        return url.from_html(body, source=entry_url)

    def parse_entry(self, entry):
        """
        Parse an entry in an RSS feed.
        """
        entry_url = self.get_url(entry)

        # merge description with body
        body = self.get_body(entry)
        description = self.get_description(entry)
        if not body:
            body = description
            description = None

        return {
            'id': entry.id,
            'url': entry_url,
            'domain': url.get_domain(entry_url),
            'body':  html.prepare(body, entry_url),
            'title': self.get_title(entry),
            'description': html.prepare(description, entry_url),
            'tags': self.get_tags(entry),
            'authors': self.get_authors(entry),
            'created': self.get_created(entry),
            'img_url': self.get_img_url(entry, body),
            'links': self.get_links(body, entry_url)
        }

    def run(self):
        """
        Parse an RSS Feed.
        """
        f = feedparser.parse(self.feed_url)
        for entry in f.entries:
            yield self.parse_entry(entry)
