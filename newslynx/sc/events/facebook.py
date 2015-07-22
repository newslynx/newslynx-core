from collections import defaultdict
from datetime import datetime
from newslynx.sc import SousChef
from newslynx.lib.facebook import Facebook


class SCFacebookEvent(SousChef):

    timeout = 300

    def _fmt(self, event):
        new = defaultdict()
        for k, v in event.iteritems():
            if isinstance(v, dict):
                new.update(self._fmt(v))
            else:
                if isinstance(v, list):
                    v = ", ".join([str(vv) for vv in v])
                elif isinstance(v, datetime):
                    v = v.date().isoformat()
                new[k] = v
        return new

    def connect(self):
        """
        Connect to twitter. Raise an error if user has not authenticated.
        """
        tokens = self.auths.get('facebook', None)
        if not tokens:
            raise Exception('This Sous Chef requires a Facebook Authorization.')
        self.facebook = Facebook()
        try:
            self.facebook.connect(**tokens)
        except Exception as e:
            raise Exception(
                'Error Connecting to Facebook: {}'.format(e.message))

    def format(self, obj):
        """
        For now all of these options are standard to twitter events.
        """
        # set the status.
        obj['status'] = self.options.get('event_status', 'pending')

        # TODO: Make formatting more elegant.
        if self.options.get('set_event_title', None):
            obj['title'] = self.options.get(
                'set_event_title').format(**self._fmt(obj))

        if self.options.get('set_event_description', None):
            obj['description'] = self.options.get(
                'set_event_description').format(**self._fmt(obj))

        if self.options.get('set_event_tag_ids', None) and \
           len(self.options.get('set_event_tag_ids')):

            obj['tag_ids'] = self.options.get('set_event_tag_ids')

        # hack because the app cant handle this field being a list.
        if self.options.get('set_event_content_items', None):
            if 'content_item_ids' not in obj:
                obj['content_item_ids'] = []
            for c in self.options.get('set_event_content_items', []):
                if isinstance(c, dict):
                    if c.get('id', None):
                        obj['content_item_ids'].append(c.get('id'))
                elif isinstance(c, int):
                    obj['content_item_ids'].append(c)
        # filter links.
        if self.options.get('must_link', False) \
           and not len(obj.get('links', [])):
            return None
        return obj

    def setup(self):
        """
        Connect to facebook.
        """
        self.connect()

    def load(self, data):
        """
        Bulk load Facebook Posts.
        """
        to_post = list(data)
        if len(to_post):
            status_resp = self.api.events.bulk_create(
                data=to_post,
                must_link=self.options.get('must_link'),
                recipe_id=self.recipe_id)
            return self.api.jobs.poll(**status_resp)


class Page(SCFacebookEvent):
    """
    Grab Events from a single or list of facebook pages.
    """
    def fetch(self):
        self.ids = defaultdict(list)
        q = self.options.pop('search_query', None)

        # accept list or not.
        page_ids = self.options.get('page_id')
        if not isinstance(page_ids, list):
            page_ids = [page_ids]

        # search all.
        for page_id in page_ids:

            # get since id.
            since_id = self.last_job.get(page_id, None)

            page = self.facebook.page_to_events(
                page_id=page_id,
                since_id=since_id
            )
            for event in page:

                # keep track of IDS
                self.ids[page_id].append(event['source_id'])

                if q:
                    tests = []
                    tests.append(q.match(event['description']))
                    tests.append(q.match(event['body']))
                    tests.append(q.match(event['links']))
                    if any(tests):
                        yield event
                else:
                    yield event

    def run(self):
        """
        Main run.
        """
        for event in self.fetch():
            event = self.format(event)
            if event:
                yield event

    def teardown(self):
        # keep track of since ids.
        if len(self.ids.keys()):
            self.next_job = {pid: max(ids) for pid, ids in self.ids.iteritems()}
