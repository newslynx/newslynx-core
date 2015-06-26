from hashlib import md5

from newslynx.core import rds
from newslynx.lib import dates
from newslynx.lib.serialize import (
    obj_to_pickle, pickle_to_obj)


class CacheResponse(object):

    """
    A class that we return from a cache request.
    """

    def __init__(self, key, value, last_modified, is_cached):
        self.key = key
        self.value = value
        self.last_modified = last_modified
        self.is_cached = is_cached

    @property
    def age(self):
        if self.is_cached:
            return (dates.now() - self.last_modified).seconds
        return 0

    def to_dict(self):
        return {
            'key': self.key,
            'last_modified': self.last_modified,
            'age': self.age,
            'is_cached': self.is_cached
        }


class Cache(object):

    """
    An abstract Cache object to inherit from.
    """
    redis = rds
    ttl = 84600  # 1 day
    key_prefix = None

    def __init__(self, debug=False):
        self.debug = debug

    def serialize(self, obj):
        """
        The function for serializing the object
        returned from `get` to a string.
        """
        return obj_to_pickle(obj)

    def deserialize(self, s):
        """
        The function for deserializing the string
        returned from redis
        """
        return pickle_to_obj(s)

    def work(self, *args, **kw):
        """
        The function for doing the work.
        """
        raise NotImplemented

    @classmethod
    def flush(cls):
        """
        Flush this cache.
        """
        for k in cls.redis.keys():
            if k.startswith(cls.key_prefix):
                cls.redis.delete(k)

    def exists(self, *args, **kw):
        return self.redis.get(self.format_key(*args, **kw)) is not None

    def invalidate(self, *args, **kw):
        """
        Remove a key from the cache.
        """
        self.redis.delete(self.format_key(*args, **kw))

    def format_key(self, *args, **kw):
        """
        Formatting the fx like this allows us
        to modify it's behavior.
        """
        return self._format_key(*args, **kw)

    def _format_key(self, *args, **kw):
        """
        Format a unique key for redis.
        """
        hash_keys = []
        for a in sorted(args):
            hash_keys.append(str(a))
        for k, v in sorted(kw.items()):
            hash_keys.append(str(v))

        hash_str = md5("".join(hash_keys)).hexdigest()
        return "{}:{}".format(self.key_prefix, hash_str)

    def get(self, *args, **kw):
        """
        The main get/cache function.
        """
        # get a custom ttl, fallback on default
        ttl = kw.pop('ttl', self.ttl)

        # format the key
        key = self.format_key(*args, **kw)

        # last modified key
        lm_key = "{}:last_modified".format(key)

        # attempt to get the object from redis
        if not self.debug:
            obj = self.redis.get(key)
        else:
            obj = None

        # if it doesn't exist, proceed with work
        if not obj:

            # not cached
            is_cached = False

            obj = self.work(*args, **kw)

            # if the worker returns None, break out
            if not obj:
                return CacheResponse(key, obj, None, False)

            # set the object in redis at the specified
            # key with the specified ttl
            self.redis.set(key, self.serialize(obj), ex=ttl)

            # set the last modified time
            last_modified = dates.now()
            self.redis.set(lm_key, last_modified.isoformat(), ex=ttl)

        else:
            # is cached
            is_cached = True

            # if it does exist, deserialize it.
            obj = self.deserialize(obj)

            # get the cached last modified time
            last_modified = dates.parse_iso(self.redis.get(lm_key))

        return CacheResponse(key, obj, last_modified, is_cached)
