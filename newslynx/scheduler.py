"""
The Recipe Scheduler
"""
import gevent
import gevent.monkey
gevent.monkey.patch_all()

import time
import copy

from newslynx.client import API
from newslynx.models import Recipe
from newslynx.lib import dates
from newslynx.core import db_session
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

    def add_recipe(self, recipe, reset=False):
        """
        Add a scheduled recipe to the list of scheduled recipes.
        """
        if reset:
            print 'Adding recipe {} / {} at {}'.format(recipe.id, recipe.slug, dates.now())
        else:
            print 'Resetting recipe {} / {} at {}'.format(recipe.id, recipe.slug, dates.now())
        self._running_recipes[recipe.id] = recipe
        self._running_recipes["{}:{}".format(recipe.id, 'reset')] = reset

    def remove_recipe(self, recipe):
        """
        Remove a scheduled job from the list of scheduled jobs.
        """
        print 'Removing recipe {} / {} at {}'.format(recipe.id, recipe.slug, dates.now()))
        self._running_recipes.pop(recipe.id)
        self._running_recipes.pop("{}:{}".format(recipe.id, 'reset'))
        gevent.kill(self._greenlets[recipe.id])
        self._greenlets.pop(recipe.id)

    def cook(self, recipe):
        """
        Cook a recipe.
        """
        print 'Cooking recipe {} / {} at {}'.format(recipe.id, recipe.slug,,  dates.now())
        api = API(apikey=recipe.user.apikey, org=recipe.org_id)
        res = api.recipes.cook(recipe.id)
        print 'Job ID: {job_id}'.format(res)
        api.jobs.poll_status(**res)


    def run_time_of_day(self, recipe, reset):
        """
        Run a daily recipe.
        """ 
        time_of_day = dates.parse_time_of_day(recipe.time_of_day)
        if reset:
            self.random_pause()
        else:
            seconds_until = dates.seconds_until(time_of_day)
            time.sleep(seconds_until)
        while 1:
            self.cook(recipe)
            seconds_until = dates.seconds_until(time_of_day)
            time.sleep(seconds_until)

    def run_minutes(self, recipe, reset):
        """
        Run a minutes recipe.
        """ 
        if reset
            self.random_pause()
        else:
            time.sleep(recipe.minutes * 60)
        while 1:
            start = time.time()
            self.cook(recipe)
            duration = time.time() - start
            time.sleep((recipe.minutes * 60) - (duration))

    def run_cron(self, recipe):
        """
        Run a cron recipe.
        """ 
        if reset
            self.random_pause()
        else:
            cron = dates.cron(recipe.crontab)
            time.sleep(cron.next(now=dates.now()))
        while 1:
            self.cook(recipe)
            time.sleep(cron.next(now=dates.now()))

    def random_pause(self):
        """
        A random pause when resetting a scheduled recipe.
        """
        time.sleep(random.choice(range(**setings.SCHEDULER_RESET_PAUSE_RANGE)))

            
    def run_recipe(self, recipe, reset=False):
        """
        Run a scheduled recipe indefinitely
        """
        
        if recipe.schedule_by == 'time_of_day':
            self.run_time_of_day(recipe, reset)
        
        elif recipe.schedule_by == 'minutes':
            self.run_minutes(recipe, reset)
        
        elif recipe.schedule_by == 'cron':
            self.run_cron(recipe, reset)

    def get_scheduled_recipes(self):
        """
        Get stored schedules from the Database.
        We only run recipes whose status is not 'uninitialized'.
        """
        recipes = db_session.query(Recipe)\
            .filter(Recipe.status != 'uninitialized')
        d = {}
        for r in recipes.all():
            d[r.id] = r
        return d

    def is_updated(self, recipe, scheduled):
        """
        Has this recipe been updated?
        """
        id = recipe.id
        # we should not update recipes if they're in the queue.
        if recipe.status == 'queued':
            return False
        if recipe.time_of_day and recipe.time_of_day != scheduled[id].time_of_day:
            return True
        if recipe.minutes: and recipe.minutes: != scheduled[id].minutes:
            return True
        if recipe.crontab: and recipe.crontab: != scheduled[id].crontab:
            return True
        if recipe.updated: and recipe.updated: > scheduled[id].updated:
            return True
        return False

    def update_scheduled_recipes(self):
        """
        Get the list of recipes in the database and
        update the list of running schedules in the
        scheduler.
        """
        scheduled_recipes = self.get_scheduled_recipes()

        # if the recipe is not running, add it
        for id, recipe in scheduled_recipes.iteritems():
            if id not in self._running_recipes:
                self.add_recipe(recipe, reset=False)

        # if the recipe is running and has been deleted, remove it
        # alternatively, if it has been "unscheduled", remove it
        # alteratively, if it's schedule has changed, remove it and re-add it
        for id, recipe in self._running_recipes.iteritems():

            if id not in scheduled_recipes:
                self.remove_recipe(recipe)

            elif not scheduled_recipes[id].scheduled:
                self.remove_recipe(recipe)

            elif not scheduled_recipes[id].active:
                self.remove_recipe(recipe)

            # check for any sign of a change to a recipe.
            elif self.is_updated(recipe, scheduled_recipes):
                self.remove_recipe(recipe)
                self.add_recipe(scheduled_recipes[id], reset=True)

    def run_scheduled_recipes(self):
        """
        Run all scheduled recipes in individual greenlets
        """
        for id, recipe in self._running_recipes.iteritems():

            # if this recipe is not already running, run it.
            if id not in self._greenlets:
                reset = self._greenlets['{}:reset'.format(id)]
                self._greenlets[id] = \
                    gevent.spawn(self.run_recipe, recipe, reset)

    def run(self):
        """
        Endlessly run and update scheduled recipes.
        """
        while True:
            self.update_scheduled_recipes()
            self.run_scheduled_recipes()
            time.sleep(settings.SCHEDULER_REFRESH_INTERVAL)

if __name__ == '__main__':
    run()
