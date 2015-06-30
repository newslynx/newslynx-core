"""
Utilities for initializing NewsLynx
"""
import os

from newslynx.lib.serialize import yaml_to_obj
from newslynx.exc import ConfigError
from newslynx import settings
from newslynx.models import sous_chef_schema
from newslynx.util import recursive_listdir, here


# directory of built-in sous chefs
SOUS_CHEF_DIR = here(__file__, 'sc')

# directory of built-in sql functions
SQL_DIR = here(__file__, 'sql')


def _load_config_file(fp):
    """
    Attempt to load a file or raise a ConfigError
    """
    try:
        return yaml_to_obj(open(fp).read())
    except Exception as e:
        raise ConfigError(
            "There was an error loding config '{}'.\n"
            "Here is the error: \n{}"
            .format(fp, e.message))


def _is_config_file(fp):
    """
    Check if a file can be parsed as yaml.
    """
    return (
        fp.endswith('json') or
        fp.endswith('yaml') or
        fp.endswith('yml')
    )


def load_sous_chef(fp):
    """
    Load and validate a sous chef config file.
    """
    sc = _load_config_file(fp)
    return sous_chef_schema.validate(sc)


def load_sous_chefs():
    """
    Get all internal and user-specified sous chef configurations.
    """

    # internal sous chefs
    for fp in recursive_listdir(SOUS_CHEF_DIR):
        if _is_config_file(fp):
            yield load_sous_chef(fp)

    # # user-generated sous-chefs.
    # if hasattr(settings, 'SOUS_CHEFS_DIR'):
    #     sous_chef_dir = settings.SOUS_CHEFS_DIR

    #     if sous_chef_dir.startswith('~'):
    #         sous_chef_dir = \
    #             os.path.expanduser(sous_chef_dir)

    #     if not os.path.exists(sous_chef_dir):
    #         raise ConfigError(
    #             "'{}' was explicitly declared as "
    #             "the sous_chef_dir but could "
    #             "not be found."
    #             .format(sous_chef_dir)
    #         )

    # else:
    #     sous_chef_dir = os.path.expanduser(
    #         '~/.newslynx/sous-chefs/')

    # if os.path.exists(sous_chef_dir):
    #     for fp in recursive_listdir(sous_chef_dir):
    #         if _is_config_file(fp):
    #             yield load_sous_chef(fp)


def load_default_tags():
    """
    Get all default tags for specified in the conf
    """
    # user-generated sous-chefs.
    if hasattr(settings, 'DEFAULT_TAGS'):
        default_tags = settings.DEFAULT_TAGS
        if default_tags.startswith('~'):
            default_tags = \
                os.path.expanduser(default_tags)
        if not os.path.exists(default_tags):
            path = "/".join(default_tags.split("/")[-1])
            try:
                os.makedirs(path)
            except OSError:
                pass
            with open(default_tags, 'wb') as f:
                f.write('-')
    else:
        default_tags = os.path.expanduser(
            '~/.newslynx/defaults/tags.yaml')

    if os.path.exists(default_tags):
        tags = _load_config_file(default_tags)
        if not isinstance(tags, list):
            raise ConfigError(
                'Default tags config must be a list of objects.'
            )
        for t in tags:
            yield t


def load_default_recipes():
    """
    Get all default tags for organizations specified in the conf.
    """
    # user-generated sous-chefs.
    if hasattr(settings, 'DEFAULT_RECIPES'):
        default_recipes = settings.DEFAULT_RECIPES

        if default_recipes.startswith('~'):
            default_recipes = \
                os.path.expanduser(default_recipes)

        if not os.path.exists(default_recipes):
            raise ConfigError(
                "'{}' was explicitly declared as "
                "the default_recipes config but could "
                "not be found."
                .format(default_recipes)
            )

    else:
        default_recipes = os.path.expanduser(
            '~/.newslynx/defaults/recipes.yaml')

    if os.path.exists(default_recipes):
        recipes = _load_config_file(default_recipes)
        if not isinstance(recipes, list):
            raise ConfigError(
                'Default recipe config files must contain a list of objects.'
            )
        for r in recipes:
            yield r


def load_sql():
    """
    Get all sql files.
    """
    for fp in sorted(list(recursive_listdir(SQL_DIR))):
        if fp.endswith('sql'):
            yield open(fp).read()
