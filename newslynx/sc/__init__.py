from newslynx.client import API
from newslynx.exc import SousChefInitError
from collections import defaultdict


class SousChef(object):

    """
    A SousChef gets an org, a user's apikey, and a recipe
    and modifies NewsLynx via it's API.
    """

    def __init__(self, *kw):
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
        return True

    def teardown(self):
        return True

    def cook(self):
        """
        The SousChef's workflow.
        """
        self.setup()
        self.run()
        self.teardown()
