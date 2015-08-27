"""
Utilities for initializing NewsLynx
"""
import os
import logging

from newslynx.lib.serialize import yaml_to_obj
from newslynx.exc import ConfigError
from newslynx.core import settings
from newslynx.models import sous_chef_schema
from newslynx.util import recursive_listdir, here

log = logging.getLogger(__name__)

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
    t1 = (
        fp.endswith('json') or
        fp.endswith('yaml') or
        fp.endswith('yml')
    )
    fp_name = fp.split('/')[-1]
    t2 = not (fp_name.startswith('_') or fp_name.startswith('.'))
    return t1 and t2


def load_sous_chefs(sous_chef_dir=None, incl_internal=True):
    """
    Get all internal and user-specified sous chef configurations.
    """
    found = False

    # user-generated sous-chefs.
    if not sous_chef_dir:
        if hasattr(settings, 'SOUS_CHEFS_DIR'):
            sous_chef_dir = settings.SOUS_CHEFS_DIR

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

    def findsc(sous_chef_dir):

        # internal sous chefs
        if incl_internal:
            for fp in recursive_listdir(SOUS_CHEF_DIR):
                if _is_config_file(fp):
                    sc = sous_chef_schema.load(fp)
                    if 'slug' in sc:
                        yield sc, fp

        # sous chef modules.
        if os.path.exists(sous_chef_dir):
            for fp in recursive_listdir(sous_chef_dir):
                if _is_config_file(fp):
                    sc = sous_chef_schema.load(fp)
                    if 'slug' in sc:
                        yield sc, fp

    for sc, fp in findsc(sous_chef_dir):
        found = True
        yield sc, fp

    if not found:
        log.warning(
            "'{}' was explicitly declared as "
            "the sous_chef_dir but no sous chefs could "
            "not be found inside."
            .format(sous_chef_dir))


def load_default_tags(t='tags'):
    """
    Get all default tags for specified in the conf
    """
    return load_defaults(t)


def load_default_recipes(t='recipes'):
    """
    Get all recipes specified in the conf.
    """
    return load_defaults(t)


def load_default_templates(t='templates'):
    """
    Load default templates.
    """
    return load_defaults(t)


def load_default_reports(t='reports'):
    """
    Load default templates.
    """
    return load_defaults(t)


def load_sql():
    """
    Get all sql files.
    """
    for fp in sorted(list(recursive_listdir(SQL_DIR))):
        if fp.endswith('sql'):
            yield open(fp).read()


def load_defaults(t):
    """
    Lookup a defaults config file
    """
    # user-generated sous-chefs.
    a = "DEFAULT_{0}".format(t.upper())
    defs = None
    if hasattr(settings, a):
        defs = getattr(settings, a)
        if defs.startswith('~'):
            defs = os.path.expanduser(defs)
        if not os.path.exists(defs):
            path = "/".join(defs.split("/")[-1])
            try:
                os.makedirs(path)
            except OSError:
                pass
            with open(defs, 'wb') as f:
                f.write('-')
    else:
        defs = os.path.expanduser(
            '~/.newslynx/defaults/{0}.yaml'
            .format(t))

    if os.path.exists(defs):
        items = _load_config_file(defs)
        if not isinstance(items, (list)):
            raise ConfigError(
                'Default {0} config must be a list of objects.'.format(t)
            )
        return items
    else:
        raise ConfigError(
            'No default {0} could be found in {1}'.format(t, defs)
        )
