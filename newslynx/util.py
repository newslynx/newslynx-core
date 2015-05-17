"""
Utilities used throughout the module.
"""
import os
import collections
import random

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
        n = random.choice(range(1, 1000000))
    return hashids.encode(n)
