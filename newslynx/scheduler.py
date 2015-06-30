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
from newslynx.logs import ColorLog

class RecipeScheduler:

    """
    A dynamic, in-memory scheduling daemon that runs recipes in greenlets and 
    responds to updates.
    """

    def __init__(self, **kwargs):
        self._running_recipes = {}
        self._greenlets = {}
        self.jigger = kwargs.get('jigger', settings.SCHEDULER_RESET_PAUSE_RANGE)
        self.log = kwargs.get('log', ColorLog(**kwargs))
        self.org_id = kwargs.get('org_id', None)

    def set_session(self):
        self.session = gen_session()

    def fmt_recipe(self, recipe):
        return "< {} | {} | {} | {} >"\
            .format(recipe.org.slug, recipe.id, recipe.slug, recipe.schedule_by)

    def add_recipe(self, recipe, reset=False):
        """
        Add a scheduled recipe to the list of scheduled recipes.
        """
        if not reset:
            self.log.info('adding {} '
                .format(self.fmt_recipe(recipe)))
        else:
            self.log.error('resetting {}'
                .format(self.fmt_recipe(recipe)))
        self._running_recipes['{}:reset'.format(recipe.id)] = reset        
        self._running_recipes[recipe.id] = recipe

    def remove_recipe(self, recipe, **kw):
        """
        Remove a scheduled job from the list of scheduled jobs.
        """
        
        if kw.get('log', True):
            self.log.error('removing {} '
                .format(self.fmt_recipe(recipe)))
        self._running_recipes.pop(recipe.id)
        self._running_recipes.pop('{}:reset'.format(recipe.id))
        greenlet = self._greenlets.pop(recipe.id)
        if greenlet:
            gevent.kill(greenlet)

    def reset_recipe(self, recipe):
        """
        Reset a recipe.
        """
        self.remove_recipe(recipe, log=False)
        self.add_recipe(recipe, reset=True)

    def cook(self, recipe):
        """
        Cook a recipe.
        """
        self.log.info('cooking {}'
            .format(self.fmt_recipe(recipe)), color='lightmagenta_ex')
        
        start = time.time()

        # api connection.
        api = API(apikey=recipe.user.apikey, org=recipe.org_id)
                
        # cook the recipe
        try:
            job = api.recipes.cook(recipe.id)
        
        except Exception as e:
            self.log.error('error {}'.format(self.fmt_recipe(recipe)))
            self.log.exception(e, tb=True)

        else:
            self.log.warning('running {} job {job_id}'
                .format(self.fmt_recipe(recipe), **job), color='lightmagenta_ex')

            # poll the job's status
            for res in api.jobs.poll(**job):
                self.log.warning(res)
            duration = round((time.time() - start), 2)
            self.log.info('cooked {} in {}s'
                .format(self.fmt_recipe(recipe), duration), color='lightmagenta_ex')

    def run_time_of_day(self, recipe, reset):
        """
        Run a daily recipe.
        """ 
        
        time_of_day = dates.parse_time_of_day(recipe.time_of_day)
        
        # lock to org's timezone.
        pause = dates.seconds_until(time_of_day, now=recipe.org.now) 

        if reset:
            pause = min([self.min_pause, pause, self.random_pause()])

        self.log.warning('first run of {} in {}s'
            .format(self.fmt_recipe(recipe), round(pause, 2)))
        time.sleep(pause)

        runs = 1
        while 1:
            runs += 1
            self.cook(recipe)
            # lock to org's timezone.
            pause = dates.seconds_until(time_of_day,  now=recipe.org.now)
            self.log.warning('run #{} of {} in {}s'
                .format(runs, self.fmt_recipe(recipe), round(pause, 2)))
            time.sleep(pause)

    def run_minutes(self, recipe, reset):
        """
        Run a minutes recipe.
        """ 
        pause = recipe.minutes * 60
        if reset:
            pause = min([pause, self.random_pause()])

        self.log.warning('first run of {} in {}s'
            .format(self.fmt_recipe(recipe), round(pause, 2)))
        time.sleep(pause)

        runs = 1
        while 1:
            runs += 1
            # account for latency.
            start = time.time()
            self.cook(recipe)
            duration = time.time() - start
            pause = (recipe.minutes * 60) - duration
            self.log.warning('run #{} of {} in {}s'
                .format(runs, self.fmt_recipe(recipe), round(pause, 2)))
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

        self.log.warning('first run of {} in {}s'
            .format(self.fmt_recipe(recipe), round(pause, 2)))
        time.sleep(pause)

        runs = 1
        while 1:
            runs += 1
            self.cook(recipe)
            # lock to org's timezone.
            pause = cron.next(now=recipe.org.now)
            self.log.warning('run #{} of {} in {}s'
                .format(runs, self.fmt_recipe(recipe), round(pause, 2)))
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
            .filter(Recipe.status != 'uninitialized')\
            .filter(Recipe.status != 'inactive')\
            .filter(Recipe.schedule_by != 'unscheduled')

        # allow this daemon to focus on one org in particular
        if self.org_id:
            recipes = recipes.filter_by(org_id=self.org_id)
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

        # we should update recipes if their schedule has changed.
        if recipe.schedule_by and recipe.schedule_by != scheduled.schedule_by:
            return True
        if recipe.time_of_day and recipe.time_of_day != scheduled.time_of_day:
            return True
        if recipe.minutes and recipe.minutes != scheduled.minutes:
            return True
        if recipe.crontab and recipe.crontab != scheduled.crontab:
            return True
        
        # we should update recipes if their core options have changed
        if recipe.options_hash != scheduled.options_hash:
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
        for id, recipe in self._running_recipes.items():
            if 'reset' in str(id):
                continue

            if id not in scheduled_recipes:
                self.remove_recipe(recipe)

            elif not scheduled_recipes[id].scheduled:
                self.remove_recipe(recipe)

            elif not scheduled_recipes[id].active:
                self.remove_recipe(recipe)

            # check for any sign of a change to a recipe.
            elif self.is_updated(recipe, scheduled_recipes[id]):
                self.reset_recipe(scheduled_recipes[id])

    def run_scheduled_recipes(self):
        """
        Run all scheduled recipes in individual greenlets
        """
        for id, recipe in self._running_recipes.iteritems():
            if 'reset' in str(id):
                continue
            
            # if this recipe is not already running, run it.
            if id not in self._greenlets:
                reset = self._running_recipes['{}:reset'.format(id)]
                self._greenlets[id] = \
                    gevent.spawn(self.run_recipe, recipe, reset)

    def run(self, **kw):
        """
        Endlessly run and update scheduled recipes.
        """
        interval = round(float(kw.get('interval', settings.SCHEDULER_REFRESH_INTERVAL)), 2)
        self.log.info('starting with refresh interval of {}s'.format(interval))
        while 1:
            self.set_session()
            self.update_scheduled_recipes()
            self.run_scheduled_recipes()
            time.sleep(interval)
            self.session.flush()
            self.log.info('refreshing'.format(interval))

