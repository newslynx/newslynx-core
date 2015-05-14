from collections import defaultdict

from addict import Dict

from newslynx.client import API


class SousChef(object):

    """
    A SousChef gets an org, a user's apikey, and a recipe
    and modifies NewsLynx via it's API.
    """

    def __init__(self, user, org, recipe):

        # api connection
        self.api = API(apikey=user.apikey, org=org.id)

        # full org object
        self.org = Dict(org.to_dict(
            incl_settings=True,
            settings_as_dict=True,
            incl_authorizations=True,
            incl_users=True))

        # options for this recipe
        self.options = Dict(recipe.options)

        # passthrough options between jobs.
        self.last_job = Dict(recipe.last_job)
        self.next_job = Dict(defaultdict())

    def setup(self):
        return True

    def run(self):
        raise NotImplementedError

    def teardown(self):
        return True

    def cook(self):
        """
        The SousChef's workflow.
        """
        self.setup()
        self.run()
        self.teardown()
