from HTMLParser import HTMLParser
from collections import defaultdict
from datetime import datetime
import time

from praw import Reddit
from praw.handlers import MultiprocessHandler

from newslynx.lib import dates
from newslynx.lib import url
from newslynx.sc import SousChef
from newslynx.util import uniq
from newslynx import settings


class SCRedditEvent(SousChef):

    def setup(self):
        self.reddit = Reddit(user_agent=settings.REDDIT_USER_AGENT)
        self._get_link_lookup()

    def _get_link_lookup(self):
        """
        Get an org's content item id lookups.
        """
        self.lookup = defaultdict(list)
        for c in self.api.orgs.simple_content():
            self.lookup[c['url']].append([c['id']])

    def _fmt(self, tweet):
        new = defaultdict()
        for k, v in tweet.iteritems():
            if isinstance(v, dict):
                new[k] = self._fmt(v)
            elif isinstance(v, list):
                new[k] = ", ".join([str(vv) for vv in v])
            elif isinstance(v, datetime):
                new[k] = v.date().isoformat()
            else:
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
        event['content_item_ids'] = uniq(event['content_item_ids'])
        # if self.options.get('must_link', False) and not len(event['content_item_ids']):
        #     return None
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

    def reconcile_urls_from_html(self, html):
        """
        Extract and prepare urls from html.
        """
        urls = list()
        for u in url.from_html(self._unescape(html)):
            u = url.prepare(u)
            if u:
                urls.append(u)
        urls = uniq(urls)
        for u in urls:
            for cid in self.lookup.get(url, []):
                yield cid

    def format(self, s):
        """
        Format a reddit post as a newslynx event.
        """

        raw = {
            'created': dates.parse_ts(s.created_utc),
            'title': s.title,
            'body': s.selftext,
            'content_item_ids': list(self.reconcile_urls_from_html(s.selftext_html)),
            'source_id': s.id,
            'url': s.permalink,
            'authors': [s.author.name]
        }
        return self._format(raw)

    def run(self):
        for result in self.fetch():
            e = self.format(result)
            print "EEE", e
            if e:
                yield e

    def load(self, data):
        """
        Prepare resulting posts for bulk loading.
        """
        to_post = []
        for d in data:
            d['recipe_id'] = self.recipe_id
            to_post.append(d)
        if len(to_post):
            status_resp = self.api.events.bulk_create(
                data=to_post,
                must_link=self.options.get('must_link', False))
            return self.api.jobs.poll(**status_resp)


class Search(SCRedditEvent):
    pass


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
        ids = set()
        for query in self.queries:
            time.sleep(5)
            for result in self.reddit.search(query=query, sort='new'):
                yield result
