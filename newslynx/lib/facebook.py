"""
An newslynx adapater for Facebook to be used in Sous Chefs.
"""
import time
import copy

import facepy

from newslynx.lib import dates
from newslynx.lib import url
from newslynx.util import uniq
from newslynx import settings


class Facebook(object):

    default_kws = {
        'paginate': False,
        'since_id': None,
        'throttle': 1,
        'limit': 100,
        'wait': 1,
        'backoff': 2,
        'timeout': 30
    }

    def connect(self, **kw):

        # parse kw's
        app_id = kw.get('app_id', settings.FACEBOOK_APP_ID)
        app_secret = kw.get('app_secret', settings.FACEBOOK_APP_SECRET)
        access_token = kw.get('access_token', None)

        # if no access token, create one
        if not access_token:
            access_token = self._generate_app_access_token(app_id, app_secret)

        # return api
        self.conn = facepy.GraphAPI(access_token)

    def _generate_app_access_token(self, app_id, app_secret):
        """
        Get an extended OAuth access token.
        :param application_id: An icdsnteger describing the Facebook application's ID.
        :param application_secret_key: A string describing the Facebook application's secret key.
        Returns a tuple with a string describing the extended access token and a datetime instance
        describing when it expires.
        """
        # access tokens
        default_access_token = facepy.get_application_access_token(
            application_id=app_id,
            application_secret_key=app_secret)
        graph = facepy.GraphAPI(default_access_token)

        response = graph.get(
            path='oauth/access_token',
            client_id=app_id,
            client_secret=app_secret,
            grant_type='client_credentials')

        return url.get_query_param(response, 'access_token')

    def _catch_err(self, func, *args, **kw):
        """
        Catch Facebook API Errors, backoff, and timeout.
        """
        # get timing kwargs
        wait = kw.get('wait')
        backoff = kw.get('backoff')
        timeout = kw.get('timeout')

        # try until we timeout
        t0 = time.time()
        results = []
        while True:
            try:
                results = func(*args, **kw)
                break

            # backoff from errors
            except facepy.FacepyError as e:
                time.sleep(wait)
                wait *= backoff

                # timeout
                now = time.time()
                if now - t0 > timeout:
                    raise Exception("Timing out beacause of {0}".format(e))
        return results

    def posts(self, **kw):
        """
        Get Posts
        """
        # update kwargs with defaults
        defs = copy.copy(self.default_kws)
        defs.update(kw)
        kw = defs

        # extract page_id
        page_id = kw.get('page_id')

        # paginate
        if kw.get('page', kw.get('paginate', False)):
            kw['page'] = True

            pages = self._catch_err(self.conn.get, page_id + "/posts", **kw)
            for page in pages:
                for post in page['data']:
                    post['page_id'] = page_id
                    yield post
        else:
            page = self._catch_err(self.conn.get, page_id + "/posts", **kw)
            for post in page['data']:
                post['page_id'] = page_id
                yield post

    def post_to_event(self, post):
        """
        Convert a facebook post into a NewsLynx Event.
        """
        return FacebookPostEvent(**post).to_dict()

    def page_to_events(self, **kw):
        """
        Fetch posts from a page and transform into NewsLynx Events.
        """

        for post in self.posts(**kw):
            yield self.post_to_event(post)


class FacebookPostEvent(object):

    permalink_fmt = "https://www.facebook.com/permalink.php?id={}&story_fbid={}"

    def __init__(self, **post):
        self.post = post
        self.page_id = self.post.pop('page_id', None)

    @property
    def source_id(self):
        return self.post.get('id')

    @property
    def created(self):
        if self.post.get('updated_time'):
            return dates.parse_iso(self.post['updated_time'])
        return None

    @property
    def description(self):
        return self.post.get('description', None)

    @property
    def title(self):
        return "Facebook post from {}".format(self.page_id)

    @property
    def img_url(self):
        return self.post.get('picture', None)

    @property
    def body(self):
        return self.post.get('message')

    @property
    def authors(self):
        return [self.page_id]

    @property
    def url(self):
        if self.source_id:
            return self.permalink_fmt.format(*self.post['id'].split('_'))

    @property
    def links(self):
        """
        Extract all links
        """
        urls = []
        if self.post.get('link'):
            urls.append(self.post['link'])

        if self.post.get('source'):
            urls.append(self.post['source'])

        if self.post.get('message'):
            msg_urls = url.from_string(self.post['message'])
            urls.extend(msg_urls)

        if self.post.get('descrption'):
            desc_urls = url.from_string(self.post['message'])
            urls.extend(desc_urls)

        return uniq(urls)

    def to_dict(self):
        return {
            'source_id': self.source_id,
            'links': self.links,
            'created': self.created,
            'img_url': self.img_url,
            'description': self.description,
            'body': self.body,
            'url': self.url,
            'title': self.title,
            'authors': self.authors
        }

if __name__ == '__main__':
    fb = Facebook()
    fb.connect()
    for event in fb.page_to_events(page_id='nytimes'):
        print event
