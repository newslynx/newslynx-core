"""
Utilities used throughout the project.
"""
import os
import collections
import random
from uuid import uuid4
from hashlib import md5


def here(f, *args):
    """
    Get the current directory and absolute path of a file.
    """
    return os.path.abspath(os.path.join(os.path.dirname(f), *args))


def recursive_listdir(directory):
    """
    Recursively list files under a directory.
    """
    return (os.path.join(dp, f) for dp, dn, fn in
            os.walk(os.path.expanduser(directory)) for f in fn)


def update_nested_dict(d, u, overwrite=False):
    """
    Recursively update a nested dictionary.
    From: http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
    """
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = update_nested_dict(d.get(k, {}), v, overwrite)
            d[k] = r
        else:
            # only add it if it doesn't already exist
            if not overwrite:
                if not d.get(k):
                    d[k] = u[k]
            else:
                d[k] = u[k]
    return d


def uniq(seq, idfun=lambda x: x):
    """
    Order-preserving unique function.
    """
    # order preserving
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker in seen:
            continue
        seen[marker] = 1
        result.append(item)
    return result


def gen_uuid():
    """
    Generate a UUID.
    """
    s = str(uuid4())
    return md5(s).hexdigest()


def gen_short_uuid(n=6):
    """
    Generate a short hash id.
    """
    uuid = gen_uuid()
    start = random.choice(range(1, (len(uuid) - n)+1))
    end = start + n
    return uuid[start:end]


def chunk_list(l, n):
    """
    Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]
