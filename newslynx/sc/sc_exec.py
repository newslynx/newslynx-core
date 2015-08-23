import importlib
import types
from traceback import format_exc

from newslynx.exc import (
    SousChefExecError,
    SousChefImportError)
from newslynx.models import (
    sous_chef_schema,
    recipe_schema)


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
            raise SousChefImportError(
                '{} does not exist in module {}.'
                .format(c, module))

    except ImportError:
        raise SousChefImportError(
            "{} is not importable."
            .format(module))
    return sous_chef


def run_sous_chef(config, **kw):
    """
    Programmatically execute a sous chef given configutations
    and recipe options. Will not load data back into NewsLynx. This can
    only be done via Recipes.
    """
    try:
        # load config file
        if not isinstance(config, types.DictType):
            if isinstance(config, basestring) and \
               (config.endswith('yaml') or config.endswith('json') or
                    config.endswith('yml')):
                config = sous_chef_schema.load(config)
            else:
                msg = 'Invalid input for config: {}'.format(config)
                raise SousChefExecError(msg)
        else:
            config = sous_chef_schema.validate(config, None)

        # parse keyword arguments
        sc_opts = dict(
            org=kw.pop('org'),
            apikey=kw.pop('apikey'),
            passthrough=True,
            config=config
        )

        # format all other options as a recipe
        recipe = dict(
            status='stable',
            id=-1
        )
        recipe.update(kw)
        sc_opts['recipe'] = \
            recipe_schema.validate(recipe, config)

        # import sous chef
        SC = import_sous_chef(config['runs'])

        # initialize it with kwargs and cook
        return SC(**sc_opts).cook()

    # bubble up traceback.
    except:
        raise SousChefExecError(format_exc())
