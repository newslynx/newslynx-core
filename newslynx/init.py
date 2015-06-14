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

    # user-generated sous-chefs.
    if hasattr(settings, 'SOUS_CHEF_DIR'):
        sous_chef_dir = settings.SOUS_CHEF_DIR

        if sous_chef_dir.startswith('~'):
            sous_chef_dir = \
                os.path.expanduser(sous_chef_dir)

        if not os.path.exists(sous_chef_dir):
            raise ConfigError(
                "'{}' was explicitly declared as "
                "the sous_chef_dir but could "
                "not be found."
                .format(sous_chef_dir)
            )

    else:
        sous_chef_dir = os.path.expanduser(
            '~/.newslynx/sous-chefs/')

    if os.path.exists(sous_chef_dir):
        for fp in recursive_listdir(sous_chef_dir):
            if _is_config_file(fp):
                yield load_sous_chef(fp)


def load_default_tags():
    """
    Get all default tags for specified in the conf
    """
    # user-generated sous-chefs.
    if hasattr(settings, 'DEFAULT_TAGS_DIR'):
        default_tags_dir = settings.SOUS_CHEF_DIR

        if default_tags_dir.startswith('~'):
            default_tags_dir = \
                os.path.expanduser(default_tags_dir)

        if not os.path.exists(default_tags_dir):
            raise ConfigError(
                "'{}' was explicitly declared as "
                "the default_tags_dir but could "
                "not be found."
                .format(default_tags_dir)
            )

    else:
        default_tags_dir = os.path.expanduser(
            '~/.newslynx/defaults/tags/')

    if os.path.exists(default_tags_dir):
        for fp in recursive_listdir(default_tags_dir):
            if _is_config_file(fp):
                tag = _load_config_file(fp)

                if isinstance(tag, list):
                    for t in tag:
                        yield t

                else:
                    yield tag


def load_default_recipes():
    """
    Get all default tags for organizations specified in the conf.
    """
    # user-generated sous-chefs.
    if hasattr(settings, 'DEFAULT_RECIPES_DIR'):
        default_recipes_dir = settings.DEFAULT_RECIPES_DIR

        if default_recipes_dir.startswith('~'):
            default_recipes_dir = \
                os.path.expanduser(default_recipes_dir)

        if not os.path.exists(default_recipes_dir):
            raise ConfigError(
                "'{}' was explicitly declared as "
                "the default_recipes_dir but could "
                "not be found."
                .format(default_recipes_dir)
            )

    else:
        default_recipes_dir = os.path.expanduser(
            '~/.newslynx/defaults/recipes/')

    if os.path.exists(default_recipes_dir):
        for fp in recursive_listdir(default_recipes_dir):
            if _is_config_file(fp):
                recipe = _load_config_file(fp)
                if isinstance(recipe, list):
                    for r in recipe:
                        yield r
                else:
                    yield recipe


def load_sql():
    """
    Get all sql files.
    """
    for fp in sorted(list(recursive_listdir(SQL_DIR))):
        if fp.endswith('sql'):
            yield open(fp).read()
