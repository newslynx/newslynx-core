import gevent
import gevent.monkey
gevent.monkey.patch_all()

import time
import copy

from newslynx.client import API
from newslynx.models import Recipe
from newslynx.lib import dates
from newxlynx.core import db_session
from newslynx import settings


def run():
    """
    A shortcut for running the scheduler daemon.
    """
    RecipeScheduler().run()


class RecipeScheduler:

    """
    An in-memory scheduler daemon that runs recipes in greenlets.
    """

    def __init__(self):
        self._running_recipes = {}
        self._greenlets = {}

    def add_recipe(self, recipe):
        """
        Add a scheduled recipe to the list of scheduled recipes.
        """
        print 'Adding {} at {}'.format(recipe, dates.now())
        self._running_recipes[recipe.id] = recipe

    def remove_recipe(self, recipe):
        """
        Remove a scheduled job from the list of scheduled jobs.
        """
        print 'Removing: {} at {}'.format(recipe, dates.now())
        self._running_recipes.pop(recipe.id)
        gevent.kill(self._greenlets[recipe.id])
        self._greenlets.pop(recipe.id)

    def run_recipe(self, recipe, daily=False):
        """
        Run a scheduled recipe indefinitely
        """
        if daily:
            time_of_day = dates.parse_time_of_day(recipe.time_of_day)
            seconds_until = dates.seconds_until(time_of_day)
            time.sleep(seconds_until)
            # one day in seconds
            interval = 24 * 60 * 60

        else:
            interval = copy.copy(recipe.interval)

        while 1:
            print 'Running: {} at {}'.format(recipe, dates.now())
            api = API(apikey=recipe.user.apikey, org=recipe.org_id)
            api.recipe.run(recipe.id)
            time.sleep(interval)

    def get_scheduled_recipes(self):
        """
        Get stored schedules from the Database.
        We only run recipes whose status is not
        'running' or 'uninitialized'.
        """
        recipes = db_session.query(Recipe)\
            .filter_by(scheduled=True)\
            .filter_by(status!='uninitialized')
        d = {}
        for r in recipes.all():
            d[r.id] = r
        return d

    def update_scheduled_recipes(self):
        """
        Get the list of recipes in the database and
        update the list of running schedules in the
        scheduler.
        """
        scheduled_recipes = self.get_scheduled_recipes()

        # if the recipe is running, add it
        for id, recipe in scheduled_recipes.iteritems():
            if id not in self._running_recipes:
                self.add_recipe(recipe)

        # if the recipe is running and has been deleted, remove it
        # alternatively, if it has been "unscheduled", remove it
        # alteratively, if its schedule has changed, remove it and re-add it
        for id, recipe in self._running_recipes.iteritems():

            if id not in scheduled_recipes or not scheduled_recipes[id].scheduled:
                self.remove_recipe(recipe)

            # check for any sign of a change to a recipe.
            elif (recipe.time_of_day and recipe.time_of_day != scheduled_recipes[id].time_of_day) or \
                 (recipe.interval and recipe.interval != scheduled_recipes[id].interval) or \
                 (recipe.updated != scheduled_recipes[id].updated):
                self.remove_recipe(recipe)
                self.add_recipe(scheduled_recipes[id])

    def run_scheduled_recipes(self):
        """
        Run all scheduled recipes in individual greenlets
        """
        for id, recipe in self._running_recipes.iteritems():

            # if this recipe is not already running, run it.
            if id not in self._greenlets:

                # time of day recipe
                if recipe.time_of_day is not None:
                    self._greenlets[id] = \
                        gevent.spawn(self.run_recipe, recipe, daily=True)

                # interval recipe
                else:
                    self._greenlets[id] = \
                        gevent.spawn(self.run_recipe, recipe)

    def run(self):
        """
        Endlessly run scheduled recipes.
        """
        while 1:
            self.update_scheduled_recipes()
            self.run_scheduled_recipes()
            time.sleep(settings.SCHEDULER_INTERVAL)
