"""
Utilities used throughout the module.
"""
import os
import collections
import random
from uuid import uuid4
from hashlib import md5

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
        n = random.choice(range(1, 10000))
    return hashids.encode(n)


def gen_uuid():
    """
    Generate a UUID.
    """
    s = str(uuid4())
    return md5(s).hexdigest()


def check_plugin(m, *plugins):
    """"
    Check if a plugin has been activated.
    """
    tests = []
    for p in plugins:
        # check for optional plugins
        if hasattr(m, p) and getattr(m, p, None):
            tests.append(True)
        else:
            tests.append(False)
    return all(tests)
