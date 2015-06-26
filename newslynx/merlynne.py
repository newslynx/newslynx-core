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
    obj_to_pickle, pickle_to_obj)


log = logging.getLogger(__name__)


class Merlynne(object):

    """
    Merlynne is the boss.
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
        rds.set(kw_key, obj_to_pickle(kw), ex=self.kw_ttl)
        return kw_key

    def cook_recipe(self):
        """
        Full pipeline.
        """
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
        sc = import_sous_chef(self.sous_chef_path)

        # stash kwargs
        kw_key = self.stash_kw(job_id)

        # send it to the queue
        self.q.enqueue(
            run_sous_chef, self.sous_chef_path,
            self.recipe.id, kw_key,
            job_id=job_id, timeout=sc.timeout,
            result_ttl=self.kw_ttl)

        # return the job id
        return job_id


def run_sous_chef(sous_chef_path, recipe_id, kw_key):
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
        kw = pickle_to_obj(kw)

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
        recipe.traceback = None
        # if something is set on this object, add it.
        if len(sc.next_job.keys()):
            recipe.last_job = sc.next_job
        db.session.add(recipe)
        db.session.commit()
        return True

    except Exception as e:

        # keep track of the error.

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
        import_parts = sous_chef_path.split('.')
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
