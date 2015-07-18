"""
Reddit => Events
"""
from HTMLParser import HTMLParser
from collections import defaultdict
from datetime import datetime
import time

from praw import Reddit

from newslynx.lib import dates
from newslynx.lib import url
from newslynx.sc import SousChef
from newslynx.util import uniq
from newslynx import settings


class SCRedditEvent(SousChef):

    timeout = 240

    def setup(self):
        self.reddit = Reddit(user_agent=settings.REDDIT_USER_AGENT)

    def _fmt(self, tweet):
        new = defaultdict()
        for k, v in tweet.iteritems():
            if isinstance(v, dict):
                new.update(self._fmt(v))
            else:
                if isinstance(v, list):
                    v = ", ".join([str(vv) for vv in v])
                elif isinstance(v, datetime):
                    v = v.date().isoformat()
                new[k] = v
        return new

    def _format(self, event):
        """
        For now all of these options are standard to events.
        """

        # set the status.
        event['status'] = self.options.get('event_status', 'pending')

        # TODO: Make formatting more elegant.
        if self.options.get('set_event_title', None):
            event['title'] = self.options.get(
                'set_event_title').format(**self._fmt(event))

        if self.options.get('set_event_description', None):
            event['description'] = self.options.get(
                'set_event_description').format(**self._fmt(event))

        if self.options.get('set_event_tag_ids', None) and \
           len(self.options.get('set_event_tag_ids')):

            event['tag_ids'] = self.options.get('set_event_tag_ids')

        # hack because the app cant handle this field being a list.
        if self.options.get('set_event_content_items', None):
            if 'content_item_ids' not in event:
                event['content_item_ids'] = []
            for c in self.options.get('set_event_content_items', []):
                if isinstance(c, dict):
                    if c.get('id', None):
                        event['content_item_ids'].append(c.get('id'))
                elif isinstance(c, int):
                    event['content_item_ids'].append(c)
        if self.options.get('must_link', False) and not len(event['links']):
            return None
        return event

    def _unescape(self, htmlentities):
        """
        Unescape html entities.
        """
        if htmlentities:
            h = HTMLParser()
            return h.unescape(htmlentities)
        else:
            return ''

    def format(self, s):
        """
        Format a reddit post as a newslynx event.
        """
        links = []
        if s.selftext_html:
            h = self._unescape(s.selftext_html)
            links = [l for l in url.from_html(h, source='http://reddit.com/') if 'reddit.com' not in l]

        raw = {
            'created': dates.parse_ts(s.created_utc),
            'title': '',
            'descrption': s.title if s.selftext else None,
            'body': s.selftext if s.selftext else s.title,
            'links': uniq([s.url] + links),
            'content_item_ids': [],
            'source_id': s.id,
            'url': url.prepare(s.permalink, canonicalize=False, expand=False),
            'img_url': s.thumbnail,
            'authors': [s.author.name],
            'meta': {
                'ups': s.ups,
                'comments': len(s.comments),
                'subreddit': s.subreddit.display_name,
                'downs': s.downs,
                'score': s.score
            }
        }
        return self._format(raw)

    def run(self):
        for result in self.fetch():
            e = self.format(result)
            if e:
                yield e

    def load(self, data):
        """
        Prepare resulting posts for bulk loading.
        """
        to_post = list(data)
        if len(to_post):
            status_resp = self.api.events.bulk_create(
                data=to_post,
                must_link=self.options.get('must_link', False),
                recipe_id=self.recipe_id)
            return self.api.jobs.poll(**status_resp)


class Search(SCRedditEvent):

    def fetch(self):

        for result in self.reddit.search(
                query=self.options.get('query'),
                sort=self.options.get('sort', 'new'),
                subreddit=self.options.get('subreddit', None)):
            yield result


class SearchContentItemLinks(SCRedditEvent):

    @property
    def queries(self):
        """
        Programmatically generate search queries based on a org's domains
        """
        domains = self.org.get('domains', [])
        domains.extend(self.settings.get('short_urls', []))
        domains.extend(self.settings.get('short_domains', []))
        domains = list(set(domains))
        _queries = []
        for d in domains:
            q = 'url:{}'.format(d)
            _queries.append(q)
        if not len(_queries):
            raise Exception('This Org has no domains.')
        return uniq(_queries)

    def fetch(self):
        """
        fetch results from reddit.
        """
        self.options['must_link'] = True
        for query in self.queries:
            time.sleep(5)
            for result in self.reddit.search(query=query, sort='new'):
                yield result
