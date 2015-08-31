"""
The Recipe Scheduler
"""
import gevent
import gevent.monkey
gevent.monkey.patch_all()

import time
import copy
import random
import logging
from traceback import format_exc

from newslynx.client import API
from newslynx.models import Recipe
from newslynx.lib import dates
from newslynx.core import gen_session
from newslynx.core import settings

log = logging.getLogger(__name__)


class RecipeScheduler:

    """
    A dynamic, in-memory scheduling daemon that runs recipes in greenlets and
    responds to updates by polling the database.
    """

    def __init__(self, **kwargs):
        self.running = {}
        self.greenlets = {}
        self.jigger = kwargs.get(
            'jigger', settings.SCHEDULER_RESET_PAUSE_RANGE)
        self.org_id = kwargs.get('org_id', None)

    def random_pause(self):
        """
        A random pause when resetting a scheduled recipe.
        """
        return random.choice(range(*self.jigger))

    @property
    def min_pause(self):
        return min(self.jigger)

    def set_session(self):
        if hasattr(self, 'session'):
            self.session.close()
        self.session = gen_session()

    def fmt(self, recipe):
        return "\n\n{2} | id: {1} | org: {0}\n"\
            .format(recipe.org.slug, recipe.id, recipe.slug)

    def add(self, recipe, reset=False):
        """
        Add a scheduled recipe to the list of scheduled recipes.
        """
        if not reset:
            log.info('adding: {} '
                     .format(self.fmt(recipe)))
        else:
            log.warning('resetting: {}'
                        .format(self.fmt(recipe)))
        self.running['{}:reset'.format(recipe.id)] = reset
        self.running[recipe.id] = recipe

    def rm(self, recipe, **kw):
        """
        Remove a scheduled job from the list of scheduled jobs.
        """

        if kw.get('log', True):
            log.warning('removing: {} '
                        .format(self.fmt(recipe)))
        self.running.pop(recipe.id)
        self.running.pop('{}:reset'.format(recipe.id))
        greenlet = self.greenlets.pop(recipe.id)
        if greenlet:
            gevent.kill(greenlet)

    def reset(self, recipe):
        """
        Reset a recipe.
        """
        self.rm(recipe, log=False)
        self.add(recipe, reset=True)

    def cook(self, recipe):
        """
        Cook a recipe.
        """
        log.info('cooking: {}'.format(self.fmt(recipe)))

        start = time.time()

        # api connection.
        api = API(apikey=recipe.user.apikey, org=recipe.org_id)

        # cook the recipe
        try:
            job = api.recipes.cook(recipe.id)

        except:
            log.error('error cooking: {}'.format(self.fmt(recipe)))
            log.error(format_exc())

        else:
            log.warning('running job {job_id} for: {0}'
                        .format(self.fmt(recipe), **job))

            try:
                # poll the job's status
                for res in api.jobs.poll(**job):
                    log.warning(res)

            except:
                log.error('error loading: {}'.format(self.fmt(recipe)))
                log.error(format_exc())

            else:
                duration = round((time.time() - start), 2)
                log.info(
                    'cooked in {1}s: {0}'.format(self.fmt(recipe), duration))

    def time_of_day(self, recipe, reset):
        """
        Run a daily recipe.
        """

        time_of_day = dates.parse_time_of_day(recipe.time_of_day)

        # lock to org's timezone.
        pause = dates.seconds_until(time_of_day, now=recipe.org.now)

        if reset:
            pause = min([self.min_pause, pause, self.random_pause()])

        log.warning('first run in {1}s: {0}'
                    .format(self.fmt(recipe), round(pause, 2)))
        time.sleep(pause)

        runs = 1
        while 1:
            runs += 1
            self.cook(recipe)
            # lock to org's timezone.
            pause = dates.seconds_until(time_of_day,  now=recipe.org.now)
            log.warning('run #{0} in {2}s of: {1}'
                        .format(runs, self.fmt(recipe), round(pause, 2)))
            time.sleep(pause)

    def minutes(self, recipe, reset):
        """
        Run a minutes recipe.
        """
        pause = recipe.minutes * 60
        if reset:
            pause = min([pause, self.random_pause()])

        log.warning('first run in {1}s: {0}'
                    .format(self.fmt(recipe), round(pause, 2)))
        time.sleep(pause)

        runs = 1
        while 1:
            runs += 1
            # account for latency.
            start = time.time()
            self.cook(recipe)
            duration = time.time() - start
            pause = (recipe.minutes * 60) - duration
            log.warning('run #{0} in {2}s of: {1}'
                        .format(runs, self.fmt(recipe), round(pause, 2)))
            time.sleep(pause)

    def crontab(self, recipe, reset):
        """
        Run a crontab recipe.
        """
        cron = dates.cron(recipe.crontab)

        # lock to org's timezone.
        pause = cron.next(now=recipe.org.now)

        # reset.
        if reset:
            pause = min([self.min_pause, pause, self.random_pause()])

        log.warning('first run in {1}s: {0}'
                    .format(self.fmt(recipe), round(pause, 2)))
        time.sleep(pause)

        runs = 1
        while 1:
            runs += 1
            self.cook(recipe)
            # lock to org's timezone.
            pause = cron.next(now=recipe.org.now)
            log.warning('run #{0} in {2}s of: {1}'
                        .format(runs, self.fmt(recipe), round(pause, 2)))
            time.sleep(pause)

    def run_one(self, recipe, reset=False):
        """
        Run a scheduled recipe indefinitely
        """

        if recipe.schedule_by == 'time_of_day':
            self.time_of_day(recipe, reset)

        elif recipe.schedule_by == 'minutes':
            self.minutes(recipe, reset)

        elif recipe.schedule_by == 'crontab':
            self.crontab(recipe, reset)

    def poll(self):
        """
        Get stored schedules from the Database.
        We dont run 'uninitialized',
         `inactive`, or 'unscheduled' recipes.
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

        # dont update
        return False

    def update(self):
        """
        Get the list of recipes in the database and
        update the scheduler.
        """
        scheduled_recipes = self.poll()

        # if the recipe is not running, add it
        for id, recipe in scheduled_recipes.iteritems():
            if id not in self.running:
                self.add(recipe, reset=False)

        # if the recipe is running and has been deleted, remove it
        # alternatively, if it has been "unscheduled", remove it
        # alteratively, if it's schedule has changed, remove it and re-add it
        for id, recipe in self.running.items():
            if 'reset' in str(id):
                continue

            if id not in scheduled_recipes or \
                    not scheduled_recipes[id].scheduled or \
                    not scheduled_recipes[id].active:

                self.rm(recipe)

            # check for any sign of a change to a recipe.
            elif self.is_updated(recipe, scheduled_recipes[id]):
                self.reset(scheduled_recipes[id])

    def spawn(self):
        """
        Run all scheduled recipes in individual greenlets
        """
        for id, recipe in self.running.iteritems():
            # ignore this helper key.
            if 'reset' in str(id):
                continue

            # if this recipe is not already running, run it. ee
            if id not in self.greenlets:
                reset = self.running['{}:reset'.format(id)]
                self.greenlets[id] = \
                    gevent.spawn(self.run_one, recipe, reset)

    def run(self, **kw):
        """
        Endlessly run and update scheduled recipes.
        """
        interval = float(
            kw.get('interval', settings.SCHEDULER_REFRESH_INTERVAL))
        interval = round(interval, 2)
        log.info('starting with refresh interval of {}s'.format(interval))
        while 1:
            self.set_session()
            self.update()
            self.spawn()
            time.sleep(interval)
            self.session.flush()
            log.info('refreshing')
