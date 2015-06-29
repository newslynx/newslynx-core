"""
The Recipe Scheduler
"""
import gevent
import gevent.monkey
gevent.monkey.patch_all()

import time
import copy
import random

from newslynx.client import API
from newslynx.models import Recipe
from newslynx.lib import dates
from newslynx.core import gen_session
from newslynx import settings


class RecipeScheduler:

    """
    An in-memory scheduler daemon that runs recipes in greenlets.
    """

    def __init__(self, **kwargs):
        self._running_recipes = {}
        self._greenlets = {}
        self.refresh_interval = kwargs.get('interval', settings.SCHEDULER_REFRESH_INTERVAL)
        self.jigger = kwargs.get('jigger', settings.SCHEDULER_RESET_PAUSE_RANGE)

    def log(self, msg):
        print msg

    def add_recipe(self, recipe, reset=False):
        """
        Add a scheduled recipe to the list of scheduled recipes.
        """
        if not reset:
            msg = 'Adding {} recipe ({} / {}) at {}'\
                .format(recipe.schedule_by, recipe.id, recipe.slug, dates.now())
            self.log(msg)
        else:
            msg = 'Resetting {} recipe ({} / {}) at {}'\
            .format(recipe.schedule_by, recipe.id, recipe.slug, dates.now())
            self.log(msg)
        self._running_recipes['{}:reset'.format(recipe.id)] = reset
        self._running_recipes[recipe.id] = recipe

    def remove_recipe(self, recipe):
        """
        Remove a scheduled job from the list of scheduled jobs.
        """
        msg = 'Removing {} recipe ({} / {}) at {}'\
            .format(recipe.schedule_by, recipe.id, recipe.slug, dates.now())
        self.log(msg)
        self._running_recipes.pop(recipe.id)
        self._running_recipes.pop('{}:reset'.format(recipe.id))
        gevent.kill(self._greenlets[recipe.id])
        self._greenlets.pop(recipe.id)

    def cook(self, recipe):
        """
        Cook a recipe.
        """
        msg = 'Cooking recipe ({} / {}) at {}'\
            .format(recipe.id, recipe.slug,  dates.now())
        self.log(msg)

        # api connection.
        api = API(apikey=recipe.user.apikey, org=recipe.org_id)
        
        # queue the recipe.
        api.recipes.update(recipe.id, status='queued')
        
        # cook the recipe
        job = api.recipes.cook(recipe.id)
        self.log('Job ID: {job_id}'.format(**job))

        # poll the job's status
        for res in api.jobs.poll(**job):
            self.log(res)

    def set_session(self):
        self.session = gen_session()

    def run_time_of_day(self, recipe, reset):
        """
        Run a daily recipe.
        """ 
        
        time_of_day = dates.parse_time_of_day(recipe.time_of_day)
        
        # lock to org's timezone.
        pause = dates.seconds_until(time_of_day, now=recipe.org.now) 

        if reset:
            pause = min([self.min_pause, pause, self.random_pause()])

        self.log("{} recipe ({} / {}) will run in {} seconds"
                .format(recipe.schedule_by, recipe.id, recipe.slug, pause))
        time.sleep(pause)

        while 1:
            self.cook(recipe)
            # lock to org's timezone.
            pause = dates.seconds_until(time_of_day,  now=recipe.org.now)
            self.log("{} recipe ({} / {}) will run again in {} seconds"
                .format(recipe.schedule_by, recipe.id, recipe.slug, pause))
            time.sleep(pause)

    def run_minutes(self, recipe, reset):
        """
        Run a minutes recipe.
        """ 
        pause = recipe.minutes * 60
        if reset:
            pause = min([pause, self.random_pause()])

        self.log("{} recipe ({} / {}) will run in {} seconds"
                .format(recipe.schedule_by, recipe.id, recipe.slug, pause))
        time.sleep(pause)

        while 1:
            # account for latency.
            start = time.time()
            self.cook(recipe)
            duration = time.time() - start
            pause = (recipe.minutes * 60) - duration
            self.log("{} recipe ({} / {}) will run again in {} seconds"
                .format(recipe.schedule_by, recipe.id, recipe.slug, pause))
            time.sleep(pause)

    def run_cron(self, recipe, reset):
        """
        Run a cron recipe.
        """ 
        cron = dates.cron(recipe.crontab)
        
        # lock to org's timezone.
        pause = cron.next(now=recipe.org.now)

        # reset.
        if reset:
            pause = min([self.min_pause, pause, self.random_pause()])

        self.log("{} recipe ({} / {}) will run in {} seconds"
                .format(recipe.schedule_by, recipe.id, recipe.slug, pause))
        time.sleep(pause)

        while 1:
            self.cook(recipe)
            # lock to org's timezone.
            pause = cron.next(now=recipe.org.now)
            self.log("{} recipe ({} / {}) will run again in {} seconds"
                .format(recipe.schedule_by, recipe.id, recipe.slug, pause))
            time.sleep(pause)

    def random_pause(self):
        """
        A random pause when resetting a scheduled recipe.
        """
        return random.choice(range(*self.jigger))

    @property
    def min_pause(self):
        return min(self.jigger)
            
    def run_recipe(self, recipe, reset=False):
        """
        Run a scheduled recipe indefinitely
        """
        
        if recipe.schedule_by == 'time_of_day':
            self.run_time_of_day(recipe, reset)
        
        elif recipe.schedule_by == 'minutes':
            self.run_minutes(recipe, reset)
        
        elif recipe.schedule_by == 'crontab':
            self.run_cron(recipe, reset)

    def get_scheduled_recipes(self):
        """
        Get stored schedules from the Database.
        We only run recipes whose status is not 'uninitialized'.
        """
        recipes = self.session.query(Recipe)\
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
        if recipe.schedule_by and recipe.schedule_by != scheduled[id].schedule_by:
            return True
        if recipe.time_of_day and recipe.time_of_day != scheduled[id].time_of_day:
            return True
        if recipe.minutes and recipe.minutes != scheduled[id].minutes:
            return True
        if recipe.crontab and recipe.crontab != scheduled[id].crontab:
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
            if str(id).endswith('reset'):
                continue
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
            if str(id).endswith('reset'):
                continue
            
            # if this recipe is not already running, run it.
            if id not in self._greenlets:
                reset = self._running_recipes['{}:reset'.format(id)]
                self._greenlets[id] = \
                    gevent.spawn(self.run_recipe, recipe, reset)

    def run(self):
        """
        Endlessly run and update scheduled recipes.
        """
        while True:
            self.set_session()
            self.update_scheduled_recipes()
            self.run_scheduled_recipes()
            time.sleep(self.refresh_interval)
            self.session.flush()
