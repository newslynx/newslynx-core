from collections import defaultdict
from datetime import datetime 

from newslynx.lib.twitter import Twitter
from newslynx.sc import EventSousChef


class TwitterEventMixin(EventSousChef):

    """
    A class to inherit from for all Twitter Sous Chefs that create events.

    You should only have to overwrite `fetch`.
    """

    timeout = 1200

    def fetch(self, **kw):
        """
        Perform the API Query.
        """
        raise NotImplemented

    def filter(self, tweet):
        """
        For now all of these options are standard to twitter
        events except for users.

        By using .get() on the options, we'll effectively ignore
        sous chefs that don't have these.
        """
        tests = []

        # search links or text.
        if self.options.get('search_query', None):
            to_search = [tweet.get('body', ''), tweet.get('links', [])]
            m = self.options['search_query'].match(to_search)
            tests.append(m)

        # filter followers
        min_followers = tweet['meta'].get('followers', 0) >= \
            self.options.get('min_followers', 0)
        tests.append(min_followers)
        if all(tests):
            return tweet

    def _get_link_lookup(self):
        return {c['url']: c['id'] for c in self.api.orgs.simple_content()
                if c.get('url', None)}

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

    def format(self, tweet):
        """
        For now all of these options are standard to twitter events.
        """

        # set the status.
        tweet['status'] = self.options.get('event_status', 'pending')

        # TODO: Make formatting more elegant.
        if self.options.get('set_event_title', None):
            tweet['title'] = self.options.get(
                'set_event_title').format(**self._fmt(tweet))

        if self.options.get('set_event_description', None):
            tweet['description'] = self.options.get(
                'set_event_description').format(**self._fmt(tweet))

        if self.options.get('set_event_tag_ids', None) and \
           len(self.options.get('set_event_tag_ids')):

            tweet['tag_ids'] = self.options.get('set_event_tag_ids')

        # hack because the app cant handle this field being a list.
        if self.options.get('set_event_content_items', None):
            if 'content_item_ids' not in tweet:
                tweet['content_item_ids'] = []
            for c in self.options.get('set_event_content_items', []):
                if isinstance(c, dict):
                    if c.get('id', None):
                        tweet['content_item_ids'].append(c.get('id'))
                elif isinstance(c, int):
                    tweet['content_item_ids'].append(c)
        tweet['content_item_ids'] = list(set(tweet['content_item_ids']))
        return tweet

    def setup(self):
        tokens = self.auths.get('twitter', None)
        if not tokens:
            raise Exception('This Sous Chef requires a Twitter Authorization.')
        self.twitter = Twitter()
        try:
            self.twitter.connect(**tokens.get('value', {}))
        except Exception as e:
            raise Exception(
                'Error Connecting to Twitter: {}'.format(e.message))

    def run(self):
        self.ids = []
        for tweet in self.fetch(max_id=self.last_job.get('max_id', None)):
            # keep track of ids for this internal method.
            if isinstance(self.ids, list):
                self.ids.append(int(tweet.get('source_id', 0)))
            tweet = self.filter(tweet)
            if tweet:
                yield self.format(tweet)

    def teardown(self):
        if len(self.ids):
            self.next_job['max_id'] = max(self.ids)


class List(TwitterEventMixin):

    """
    List => Event
    """

    def fetch(self, **kw):
        # fetch tweets
        kw.update({
            'owner_screen_name': self.options.get('list_owner_screen_name'),
            'slug': self.options.get('list_slug')
        })
        self.log.info('Fetching list\n{}'.format(kw))
        return self.twitter.list_to_event(**kw)


class User(TwitterEventMixin):

    """
    User => Event
    """

    def fetch(self, **kw):
        # fetch tweets
        kw.update({
            'screen_name': self.options.get('screen_name')
        })
        self.log.info('Fetching user\n{}'.format(kw))
        return self.twitter.user_to_event(**kw)


class Search(TwitterEventMixin):

    """
    Search => Event
    """

    def fetch(self, **kw):
        # fetch tweets
        kw.update({
            'q': self.options.get('api_query'),
            'result_type': self.options.get('result_type', 'recent')
        })
        self.log.info('Searching for:\n{}'.format(kw))
        return self.twitter.search_to_event(**kw)


class SearchContentItemLinks(TwitterEventMixin):

    """
    Search an org's domains and short-domains for links to content items.
    """

    @property
    def queries(self):
        domains = self.org.get('domains', [])
        domains.extend(self.settings.get('short_urls', []))
        domains.extend(self.settings.get('short_domains', []))
        domains = list(set(domains))
        _queries = []
        for d in domains:
            term = d.replace(".", " ").strip().lower()
            q = '"{}" filter:links'.format(term)
            _queries.append(q)
        if not len(_queries):
            raise Exception('This Org has no domain.')
        return list(set(_queries))

    def fetch(self, **kw):
        self.ids = defaultdict(list)
        self.lookup = self._get_link_lookup()
        for q in self.queries:
            # fetch tweets
            kw = {
                'q': q,
                'result_type': 'recent',
                'max_id': self.last_job.get('max_ids', {}).get(q, None)
            }
            self.log.info('Searching for:\n{}'.format(kw))

            # search all tweets that link to this domain
            for tweet in self.twitter.search_to_event(**kw):
                self.ids[q].append(int(tweet.get('source_id', 0)))
                yield tweet

    def filter(self, tweet):
        # check for links to an org's content items.
        tweet['content_item_ids'] = []
        for link in tweet.get('links', []):
            if link not in self.lookup:
                continue
            tweet['content_item_ids'].append(self.lookup[link])

        # filter
        if len(tweet['content_item_ids']):
            tweet.pop('links', None)
            return tweet

    def teardown(self):
        if len(self.ids.keys()):
            max_ids = {k: max(v) for k, v in self.ids.iteritems()}
            self.next_job['max_ids'] = max_ids
        return
