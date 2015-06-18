"""
All things related to rss parsing.  We make use of feedparser which
we manage within this repository @ newslynx/lib/pkg/feedparser.py
"""
from gevent.monkey import patch_all
patch_all()
from gevent.pool import Pool

import jsonpath_rw as jsonpath

from newslynx.lib.pkg import feedparser
from newslynx.lib import dates
from newslynx.lib import author
from newslynx.lib import html
from newslynx.lib import url
from newslynx.lib import article
from newslynx.lib import network


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


def parse_entries(feed_url, domains=[]):
    """
    Parser entries from an rss feed.
    """
    f = FeedExtractor(feed_url, domains)
    return f.run()


def extract_entries(feed_url, domains=[]):
    """
    Parse entries from an rss feed and run article extraction
    an each
    """
    entries = FeedExtractor(feed_url, domains).run()
    urls = [e['url'] for e in entries if e.get('url')]
    p = Pool(len(entries))
    keys_to_merge = entries[0].keys()
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
        candidates = set()
        for path in jsonpaths:
            path_candidates = self.get_jsonpath(obj, path)

            if isinstance(path_candidates, list):
                for candidate in path_candidates:
                    if candidate:
                        candidates.add(candidate)

            elif isinstance(path_candidates, str):
                candidates.add(candidate)

        return list(candidates)

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

        titles = set()

        candidates = self.get_candidates(entry, TITLE_CANDIDATE_JSONPATH)
        for c in candidates:
            titles.add(c)

        titles = list(titles)

        if len(titles) == 0:
            return None

        if len(titles) == 1:
            return titles[0]

        titles.sort(key=len)
        return titles[-1]

    # get title
    def get_description(self, entry):
        """
        return all candidates, and parse unique
        """

        descriptions = set()

        candidates = self.get_candidates(entry, DESCRIPTION_CANDIDATE_JSONPATH)
        for c in candidates:
            descriptions.add(c)

        descriptions = list(descriptions)

        if len(descriptions) == 0:
            return None

        if len(descriptions) == 1:
            return descriptions[0]

        descriptions.sort(key=len)
        return descriptions[-1]

    # get authors
    def get_authors(self, entry):
        """
        return all candidates, and parse unique
        """

        authors = set()

        candidates = self.get_candidates(entry, AUTHOR_CANDIDATE_JSONPATH)
        for c in candidates:
            for a in author.parse(c):
                authors.add(a)

        return list(authors)

    # get images
    def get_img_url(self, entry, body):
        """
        Get the top image url.
        """
        img_urls = self.get_candidates(entry, IMG_CANDIDATE_JSONPATH)
        img_urls = list(set(img_urls))
        if len(img_urls):
            return img_urls[0]

    def get_body(self, entry):
        """
        Get all body candidates and check which one is the longest.
        """
        candidates = self.get_candidates(entry, BODY_CANDIDATE_JSONPATH)
        candidates.sort(key=len)
        if len(candidates):
            return candidates[-1]

    def get_tags(self, entry):
        """
        Get all tags.
        """
        tags = self.get_candidates(entry, TAG_CANDIDATE_JSONPATH)
        return list(set([t.upper() for t in tags if t and t != ""]))

    def get_url(self, entry):
        """
        Get the url.
        """
        # get potential candidates
        candidates = self.get_candidates(entry, URL_CANDIDATE_JSONPATH)

        # if no candidates, return an empty string
        if len(candidates) == 0:
            return None

        # test for valid urls:
        urls = set()
        for u in candidates:
            if any([d in u for d in self.domains]):
                urls.add(u)

        # if we have one or more, update return the first.
        urls = list(urls)
        urls.sort(key=len)
        if len(urls) >= 1:
            return urls[-1]

        # if we STILL haven't found anything, just
        # return the first candidate that looks like a url.
        return [u for u in urls if u.startswith('http')][0]

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
        body = self.get_body(entry)

        return {
            'url': entry_url,
            'body':  html.prepare(body, entry_url),
            'title': self.get_title(entry),
            'description': self.get_description(entry),
            # 'tags': self.get_tags(entry),
            'authors': self.get_authors(entry),
            'created': self.get_created(entry),
            'img_url': self.get_img_url(body),
            'links': self.get_links(body, entry_url),
        }

    @network.retry(attempts=2)
    def fetch_feed(self):
        return feedparser.parse(self.feed_url)

    def run(self):
        """
        Parse an Rss Feed.
        """
        f = feedparser.parse(self.feed_url)
        return map(self.parse_entry, f.entries)


if __name__ == '__main__':
    ex_entries = extract_entries('http://wisconsinwatch.org/feed/', ['wisconsinwatch.org'])
    p_entries = parse_entries('http://wisconsinwatch.org/feed/', ['wisconsinwatch.org'])
    for e, p in zip(ex_entries, p_entries):
        print e['authors'], p['authors']
        print e['url'], p['url']

