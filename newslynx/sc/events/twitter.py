"""
Twitter => Events.
"""
from collections import defaultdict
from datetime import datetime

from newslynx.lib.twitter import Twitter
from newslynx.sc import SousChef
from newslynx.util import uniq


class SCTwitterEvent(SousChef):

    """
    A class to inherit from for all Twitter Sous Chefs that create events.

    You should only have to overwrite `fetch`.
    """

    timeout = 1200

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

    def fetch(self, **kw):
        """
        Perform the API Query.
        """
        raise NotImplemented('You must implement a fetch method.')

    def filter(self, tweet):
        """
        For now all of these options are standard to twitter
        events except for users.

        By using .get() on the options, we'll effectively ignore
        sous chefs that don't have certain options.
        """
        tests = []
        if not tweet.get('source_id', None):
            tweet['source_id'] = tweet.get('url')

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
            # optionally filter
            if self.options.get('must_link', False):
                if len(tweet['links']):
                    return tweet
            return tweet

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
        return tweet

    def connect(self):
        """
        Connect to twitter. Raise an error if user has not authenticated.
        """
        tokens = self.auths.get('twitter', None)
        if not tokens:
            raise Exception('This Sous Chef requires a Twitter Authorization.')
        self.twitter = Twitter()
        try:
            self.twitter.connect(**tokens)
        except Exception as e:
            raise Exception(
                'Error Connecting to Twitter: {}'.format(e.message))

    def run(self):
        """
        Connect to twitter, fetch the lookup of content items, fetch tweets,
        filter, and format.
        """
        self.connect()
        for tweet in self.fetch(since_id=self.last_job.get('max_id', None)):
            tweet = self.filter(tweet)
            if tweet:
                yield self.format(tweet)

    def load(self, data):
        """
        Prepare resulting tweets for bulk loading.
        """
        self.ids = []
        to_post = []
        for d in data:
            self.ids.append(int(d.get('source_id', 0)))
            to_post.append(d)
        if len(to_post):
            status_resp = self.api.events.bulk_create(
                data=to_post,
                must_link=self.options.get('must_link'),
                recipe_id=self.recipe_id)
            return self.api.jobs.poll(**status_resp)

    def teardown(self):
        """
        Keep track of max id.
        """
        if len(self.ids):
            self.next_job['max_id'] = max(self.ids)


class List(SCTwitterEvent):

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


class User(SCTwitterEvent):

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


class Search(SCTwitterEvent):

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


class SearchContentItemLinks(SCTwitterEvent):

    """
    Search an org's domains and short-domains for links to content items.
    """

    @property
    def queries(self):
        """
        Programmatically generate search queries based on a org's domains
        """
        domains = self.org.get('domains', [])
        domains.extend(self.settings.get('short_urls', []))
        domains.extend(self.settings.get('short_domains', []))
        domains = uniq(domains)
        _queries = []
        for d in domains:
            term = d.replace(".", " ").strip().lower()
            q = '"{}" filter:links'.format(term)
            _queries.append(q)
        if not len(_queries):
            raise Exception('This Org has no domain.')
        return uniq(_queries)

    def fetch(self, **kw):
        """
        Fetch tweets for all queries, keeping track of max ID for
        each unique query.
        """
        # we should include embeds on this sous chef.
        setattr(self.twitter, 'incl_embed', True)

        self.qids = defaultdict(list)
        for q in self.queries:
            # fetch tweets
            kw = {
                'q': q,
                'result_type': 'recent',
                'since_id': self.last_job.get('max_ids', {}).get(q, None)
            }
            self.log.info('Searching for: {}'.format(kw))

            # search all tweets that link to this domain
            for tweet in self.twitter.search_to_event(**kw):
                self.qids[q].append(int(tweet.get('source_id', 0)))
                yield tweet

    def teardown(self):
        """
        Store max Ids.
        """
        if len(self.qids.keys()):
            max_ids = {k: max(v) for k, v in self.qids.iteritems()}
            self.next_job['max_ids'] = max_ids
        return
