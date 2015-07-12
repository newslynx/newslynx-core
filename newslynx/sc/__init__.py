from inspect import isgenerator

from newslynx.client import API
from newslynx.exc import SousChefInitError
from collections import defaultdict


class SousChef(object):

    """
    A SousChef gets an org, a user's apikey, and a recipe
    and modifies NewsLynx via it's API.
    """

    timeout = 120  # how long until this sous chef timesout?

    def __init__(self, **kw):
        # parse kwargs

        self.org = kw.get('org')
        self.recipe = kw.get('recipe')
        self.apikey = kw.get('apikey')
        self.passthrough = kw.get('passthrough', False)

        if not self.org or not self.recipe or not self.apikey:
            raise SousChefInitError(
                'A SousChef requires a "org", "recipe", and "apikey" to run.')

        # api connection
        self.api = API(apikey=self.apikey, org=self.org['id'])

        # full org object
        self.auths = self.org.pop('auths')
        self.settings = self.org.pop('settings')
        self.users = self.org.pop('users')

        # options for this recipe
        self.options = self.recipe['options']
        self.recipe_id = self.recipe['id']

        # handle cache-clears between jobs.
        self.next_job = defaultdict()
        if not self.passthrough:
            lj = self.recipe.get('last_job', None)
            if lj is None:
                self.last_job = defaultdict()
            elif not isinstance(lj, dict):
                self.last_job = defaultdict()
            else:
                self.last_job = lj
        
        # passthrough jobs should not use contextual
        # variables.
        else:
            self.last_job = defaultdict()

    def setup(self):
        return True

    def run(self):
        raise NotImplemented

    def load(self, data):
        return data

    def teardown(self):
        return True

    def cook(self):
        """
        The SousChef's workflow.
        """
        self.setup()
        data = self.run()
        # passthrough jobs should not 'load'
        if not self.passthrough:
            data = self.load(data) # load the data.
        return data

# TODO: Get Bulk Loading working here.

class ContentSousChef(SousChef):
    extract = True

    def load(self, data):
        to_post = []
        for d in data:
            d['recipe_id'] = self.recipe_id
            to_post.append(d)
        status_resp = self.api.content.bulk_create(to_post)
        return self.api.jobs.poll(**status_resp)


class EventSousChef(SousChef):

    def load(self, data):
        to_post = []
        for d in data:
            d['recipe_id'] = self.recipe_id
            to_post.append(d)
        status_resp = self.api.events.bulk_create(to_post)
        return self.api.jobs.poll(**status_resp)


class ContentTimeseriesSousChef(SousChef):

    def load(self, data):
        if isgenerator(data):
            data = list(data)
        status_resp = self.api.content.bulk_create_timeseries(data)
        return self.api.jobs.poll(**status_resp)


class ContentSummarySousChef(SousChef):

    def load(self, data):
        if isgenerator(data):
            data = list(data)
        status_resp = self.api.content.bulk_create_summary(data)
        return self.api.jobs.poll(**status_resp)
