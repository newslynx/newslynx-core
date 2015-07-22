from inspect import isgenerator

from newslynx.client import API
from newslynx.exc import SousChefInitError
from collections import defaultdict
from newslynx.logs import StdLog


class SousChef(object):

    """
    A SousChef gets an org, a user's apikey, and a recipe
    and modifies NewsLynx via it's API.
    """

    timeout = 240  # how long until this sous chef timesout?

    def __init__(self, **kw):
        # parse kwargs
        self.log = StdLog()  # TODO: logging configuration.
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
        self.next_job = defaultdict(dict)
        if not self.passthrough:
            lj = self.recipe.get('last_job', None)
            if lj is None:
                self.last_job = defaultdict(dict)
            elif not isinstance(lj, dict):
                self.last_job = defaultdict(dict)
            else:
                self.last_job = lj
        # passthrough jobs should not use contextual
        # variables.
        else:
            self.last_job = defaultdict(dict)

    def setup(self):
        return True

    def run(self):
        raise NotImplemented('A SousChef requires a `run` method.')

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
            data = self.load(data)  # load the data.
        return data