import importlib
from traceback import format_exc
import logging
import copy

from newslynx.core import db, rds, queues
from newslynx.lib import dates
from newslynx.util import gen_uuid
from newslynx import settings
from newslynx.exc import InternalServerError, MerlynneError
from newslynx.lib.serialize import (
    obj_to_pickle, pickle_to_obj)


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
        self.kw_tll = settings.MERLYNNE_KWARGS_TTL
        self.q = queues.get('recipe')
        self.redis = rds

    def stash_kw(self, job_id):
        """
        Stash the kwargs and return the redis key.
        """
        kw_key = "{}:{}".format(self.kw_prefix, job_id)
        self.redis.set(kw_key, obj_to_pickle(self.sous_chef_kwargs))
        return kw_key

    def import_sous_chef(self):
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

    def execute_sous_chef(self, kw_key):
        """
        Run the Sous Chef and handle errors.
        """
        try:
            self._execute_sous_chef(kw_key)
            return True
        except Exception as e:
            db.session.rollback()
            self.recipe.status = "error"
            self.recipe.traceback = format_exc()
            db.session.add(self.recipe)
            db.session.commit()
            return MerlynneError(e)

    def _execute_sous_chef(self, kw_key):
        """
        Do the work.
        """
        # load in kwargs
        kw = self.redis.get(kw_key)
        if not kw:
            raise InternalServerError(
                'An unexpected error occurred while attempting to run a Sous Chef.'
            )
        kw = pikcle_to_obj(kw)

        # import sous chef
        SousChef = self.import_sous_chef()

        # initialize it with kwargs
        sc = SousChef(**kw)

        # cook it.
        sc.cook()

        # update status and next job from sous chef.
        self.recipe.status = "stable"
        self.recipe.last_job = sc.next_job
        db.session.add(self.recipe)
        db.session.commit()

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


