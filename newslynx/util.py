"""
Utilities used throughout the module.
"""

import os
import collections
import random

from newslynx.lib.serialize import yaml_stream_to_obj
from newslynx.exc import ConfigError
from hashids import Hashids

# a constructor of short hashes.
hashids = Hashids()


def here(f, *args):
    """
    Get the current directory and absolute path of a file.
    """
    return os.path.abspath(os.path.join(os.path.dirname(f), *args))


def recursive_listdir(directory):
    """
    Recursively list files under a directory.
    """
    return (os.path.join(dp, f) for dp, dn, fn in os.walk(os.path.expanduser(directory)) for f in fn)


def is_config_file(fp):
    """
    Check if a file can be parsed as yaml.
    """
    return fp.endswith('json') or fp.endswith('yaml') or fp.endswith('yml')


def load_config():
    """
    Load newslynx configurations from file / env variables.
    """
    # load config file
    config_file = os.getenv('NEWSLYNX_CONFIG_FILE', '~/.newslynx/config.yaml')
    if config_file.startswith('~'):
        config_file = os.path.expanduser(config_file)

    if not os.path.exists(config_file):
        raise ConfigError(
            'No NewsLynx Config could be found at {}'.format(config_file))

    config = yaml_stream_to_obj(open(config_file))

    # update with environment variables
    for name, value in sorted(os.environ.items()):
        if name.startswith('NEWSLYNX_') and name != 'NEWSLYNX_CONFIG_FILE':
            name = name.replace('NEWSLYNX_', '').lower()
            config[name] = value
    return config


def update_nested_dict(d, u):
    """
    Recursively update a nested dictionary.
    From: http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
    """
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = update_nested_dict(d.get(k, {}), v)
            d[k] = r
        else:
            if not d.get(k):
                d[k] = u[k]
    return d


def gen_hash_id(n=None):
    """
    Generate a short hash id.
    """
    if not n:
        n = random.choice(range(1, 1000000))
    return hashids.encode(n)
