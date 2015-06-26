import importlib
from traceback import format_exc
import logging
import copy

from newslynx.core import db, rds, queues
from newslynx.models import Recipe
from newslynx.lib import dates
from newslynx.util import gen_uuid
from newslynx import settings
from newslynx.exc import InternalServerError, MerlynneError
from newslynx.lib.serialize import (
    obj_to_json, json_to_obj)


log = logging.getLogger(__name__)


class Merlynne(object):

    """
    Merlynne is the boss. She orders SousChefs to cook your Recipes.
    """
    __module__ = 'newslynx.merlynne'

    def __init__(self, **kw):
        self.recipe = kw.pop('recipe_obj')
        self.sous_chef_path = kw.pop('sous_chef_path')
        self.sous_chef_kwargs = kw
        self.kw_prefix = settings.MERLYNNE_KWARGS_PREFIX
        self.kw_ttl = settings.MERLYNNE_KWARGS_TTL
        self.result_ttl = settings.MERLYNNE_RESULTS_TTL
        self.q = queues.get('recipe')

    def stash_kw(self, job_id):
        """
        Stash the kwargs and return the redis key.
        """
        kw_key = "{}:{}".format(copy.copy(self.kw_prefix), job_id)
        kw = copy.copy(self.sous_chef_kwargs)
        rds.set(kw_key, obj_to_json(kw), ex=self.kw_ttl)
        return kw_key

    def run_sous_chef(self, kw_key):
        """
        Run the Sous Chef and handle errors.
        """
        pass

    def cook_recipe(self):

        # indicate that the recipe is running.
        self.recipe.last_run = dates.now()
        self.recipe.status = "running"
        db.session.add(self.recipe)
        db.session.commit()

        # generate a job id
        job_id = gen_uuid()

        # import the sous chef here to get the timeout
        # and raise import errors before it attempts to run
        # in the queue
        sc = self.import_sous_chef()

        # stash kwargs
        try:
            kw_key = self.stash_kw(job_id)
        except Exception as e:
            print "CANT STASH KWARGS"
            raise e
        print "ENQUEING"
        # send the job to the task queue
        print "timeout", sc.timeout
        try:
            self.q.enqueue(
                run_sous_chef, kw_key, self.recipe.id,
                job_id=job_id, timeout=sc.timeout,
                result_ttl=self.kw_ttl)
        except Exception as e:
            print format_exc()
            raise e
        return job_id


def run_sous_chef(recipe_id, sous_chef_path, kw_key):
    """
    Do the work. This exists outside the class
    in order to enable pickling.
    """
    recipe = db.session.query(Recipe).get(recipe_id)
    try:
        # load in kwargs
        kw = rds.get(kw_key)
        if not kw:
            raise InternalServerError(
                'An unexpected error occurred while attempting to run a Sous Chef.'
            )
        kw = json_to_obj(kw)

        # delete them.
        rds.delete(kw_key)

        # import sous chef
        SousChef = import_sous_chef(sous_chef_path)

        # initialize it with kwargs
        sc = SousChef(**kw)

        # cook it.
        sc.cook()

        # update status and next job from sous chef.
        recipe.status = "stable"
        recipe.last_job = sc.next_job
        db.session.add(recipe)
        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        recipe.status = "error"
        recipe.traceback = format_exc()
        db.session.add(recipe)
        db.session.commit()
        return MerlynneError(e)

def import_sous_chef(sous_chef_path):
    """
    Import a sous chef.
    """
    try:

        import_parts = self.sous_chef_path.split('.')
        module = '.'.join(import_parts[:-1])
        c = import_parts[-1]
        m = importlib.import_module(module)
        sous_chef = getattr(m, c, None)

        if not sous_chef:
            raise MerlynneError(
                '{} does not exist in module {}.'
                .format(c, module))

    except ImportError:
        raise MerlynneError(
            "{} is not importable."
            .format(module))
    return sous_chef
