"""
Merlynne is the boss. She runs sous chefs in a task queue. What.
"""
from traceback import format_exc
from inspect import isgenerator
import logging
import copy

from newslynx.core import db, rds, queues
from newslynx.models import Recipe, Org
from newslynx.lib import dates
from newslynx.util import gen_uuid
from newslynx.core import settings
from newslynx.exc import InternalServerError, MerlynneError
from newslynx.lib.serialize import (
    obj_to_pickle, pickle_to_obj)
from newslynx.sc import sc_exec
from newslynx import notify


log = logging.getLogger(__name__)


class Merlynne(object):

    """
    Dont mess with Merylnne.
    """
    __module__ = 'newslynx.merlynne'

    def __init__(self, **kw):
        self.recipe = kw.pop('recipe_obj')
        self.sous_chef_path = kw.pop('sous_chef_path')
        self.sous_chef_kwargs = kw
        self.kw_prefix = settings.MERLYNNE_KWARGS_PREFIX
        self.kw_ttl = settings.MERLYNNE_KWARGS_TTL
        self.result_ttl = settings.MERLYNNE_RESULTS_TTL
        self.passthrough = kw.get('passthrough', False)
        self.q = queues.get('recipe')

    def stash_kw(self, job_id):
        """
        Stash the kwargs and return the redis key.
        """
        kw_key = "{}:{}".format(copy.copy(self.kw_prefix), job_id)
        kw = copy.copy(self.sous_chef_kwargs)
        rds.set(kw_key, obj_to_pickle(kw), ex=self.kw_ttl)
        return kw_key

    def cook_recipe(self):
        """
        Full pipeline.
        """
        # generate a job id
        job_id = gen_uuid()

        # import the sous chef here to get the timeout
        # and raise import errors before it attempts to run
        # in the queue
        _sc = sc_exec.from_import_path(self.sous_chef_path)

        # send it to the queue
        if not self.passthrough:

            # stash kwargs
            kw_key = self.stash_kw(job_id)

            # indicate that the recipe is running.
            self.recipe.status = "queued"
            db.session.add(self.recipe)
            db.session.commit()

            self.q.enqueue(
                run, self.sous_chef_path,
                self.recipe.id, kw_key,
                job_id=job_id, timeout=_sc.timeout,
                result_ttl=self.kw_ttl)

            # return the job id
            return job_id

        # directly stream the results out.
        return run(self.sous_chef_path,
                   self.recipe.id, kw_key=None,
                   **self.sous_chef_kwargs)


def run(sous_chef_path, recipe_id, kw_key, **kw):
    """
    Do the work. This exists outside the class
    in order to enable pickling for the task queue.
    """
    recipe = db.session.query(Recipe).get(recipe_id)
    try:
        if kw_key:
            # load in kwargs
            kw = rds.get(kw_key)
            if not kw:
                raise InternalServerError(
                    'An unexpected error occurred while attempting to run a Sous Chef.'
                )
            kw = pickle_to_obj(kw)
            # delete them.
            rds.delete(kw_key)

        # import sous chef
        SousChef = sc_exec.from_import_path(sous_chef_path)

        # initialize it with kwargs
        kw['org'] = db.session\
            .query(Org).get(recipe.org.id)\
            .to_dict(incl_domains=True)
        kw['recipe'] = recipe.to_dict()
        sous_chef = SousChef(**kw)

        # indicate that the job is running
        if not kw.get('passthrough', False):
            recipe.status = 'running'
            db.session.add(recipe)
            db.session.commit()

        # cook it.
        data = sous_chef.cook()

        # passthrough the data.
        if kw.get('passthrough', False):
            return data

        # otherwise just exhaust the generator
        if isgenerator(data):
            data = list(data)

        # teardown this recipe
        sous_chef.teardown()

        # update status and next job from sous chef.
        recipe.status = "stable"
        recipe.traceback = None
        recipe.last_run = dates.now()
        if len(sous_chef.next_job.keys()):
            recipe.last_job = sous_chef.next_job
        db.session.add(recipe)
        db.session.commit()
        return True

    except:

        # always delete the kwargs.
        if kw_key:
            rds.delete(kw_key)

        if not kw.get('passthrough', False):
            db.session.rollback()
            recipe.status = "error"
            recipe.traceback = format_exc()
            recipe.last_run = dates.now()
            db.session.add(recipe)
            db.session.commit()

            # notification
            tb = format_exc()
            error_notification(recipe, tb)
            return MerlynneError(tb)

        raise MerlynneError(format_exc())


def error_notification(recipe, tb):
    """
    Send a notification of a failed recipe.
    """
    msg = """
    **Recipe** with **slug** `{slug}` failed at `{last_run}` for organization `{org_id}`.
    Here's the traceback:
    ```
    {tb}
    ```
    You can access this recipe via:

    *GET* `/api/v1/recipes/{id}?org={org_id}&apikey=<super_user_apikey>`
    """.format(tb=tb, **recipe.to_dict())

    for m in settings.NOTIFY_METHODS:
        method = notify.METHODS[m]
        method.send(msg, subject="recipes")
