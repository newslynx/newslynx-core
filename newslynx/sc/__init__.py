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

        org = kw.get('org')
        recipe = kw.get('recipe')
        apikey = kw.get('apikey')

        if not org or not recipe or not apikey:
            raise SousChefInitError(
                'A SousChef requires a "org", "recipe", and "apikey" to run.')

        # api connection
        self.api = API(apikey=apikey, org=org['id'])

        # full org object
        self.auths = org.pop('auths')
        self.settings = org.pop('settings')
        self.users = org.pop('users')
        self.org = org

        # options for this recipe
        self.options = recipe['options']
        self.recipe_id = recipe['id']

        # passthrough options between jobs.
        self.last_job = recipe['last_job']
        self.next_job = defaultdict()

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
        resp = self.load(data)
        self.teardown()
        return resp

# TODO: Get Bulk Loading working here.


class ContentSousChef(SousChef):
    extract = True

    def load(self, data):
        if isgenerator(data):
            data = list(data)
        for item in data:
            item.update({'extract': self.extract})
            self.api.content.create(**item)


class EventSousChef(SousChef):

    def load(self, data, **kw):
        if isgenerator(data):
            data = list(data)
        for item in data:
            self.api.events.create(**item)


class ContentTimeseriesSousChef(SousChef):

    def load(self, data):
        if isgenerator(data):
            data = list(data)
        status_resp = self.api.content.bulk_create_timeseries(data)
        return self.api.jobs.poll_status(**status_resp)


class ContentSummarySousChef(SousChef):

    def load(self, data):
        if isgenerator(data):
            data = list(data)
        status_resp = self.api.content.bulk_create_summary(data)
        return self.api.jobs.poll_status(**status_resp)
