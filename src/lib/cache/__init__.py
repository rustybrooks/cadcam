import bson
import datetime
import dateutil.parser
import functools
from ..api_framework import OurJSONEncoder
import json
import hashlib
import logging
import os
import pickle

# from Reputation_system.utils import redis_conn, mongo

cache_sentinel = object()
logger = logging.getLogger(__name__)

CACHE = 1
NOCACHE = 2
PRECACHE = 3
RECACHE = 4


def arg_hash(*args, **kwargs):
    # logger.warn("cache arg_hash -> %r - %r", args, kwargs)
    h = hashlib.md5()
    map(lambda x: h.update(repr(unicode(x))), args)
    map(lambda x: h.update(repr(unicode(x) + unicode(kwargs[x]))), sorted(kwargs.keys()))
    return h.hexdigest()


def default_cachefn(*args, **kwargs):
    if kwargs.get('_precache', False):
        return PRECACHE

    if kwargs.get('_nocache', False):
        return NOCACHE

    if kwargs.get('_recache', False):
        return RECACHE

    return CACHE


# a canonical cache object is a dict or dict-like object with the keys of
# key, created, value, args, kwargs
class CacheBase(object):
    def __init__(self, prefix, timeout, grace=None, keyfn=None, cachefn=None, binary=False, debug=False):
        self.prefix = prefix
        self.timeout = timeout
        self.grace = grace
        self.keyfn = keyfn or arg_hash
        self.cachefn = cachefn or default_cachefn
        self.binary = binary
        self.debug = debug

    #############################################################################
    # functions subclasses must implement

    # needs to save a canonical cache object
    def update_cache(self, key, cache):
        raise Exception('Not implemented')

    # needs to load and return a canonical cache object
    def load_cache(self, key):
        raise Exception('Not implemented')

    # needs to check for the existence of the cached object
    def exists_cache(self, key):
        raise Exception('Not implemented')

    # needs to remove item from cache
    def delete_cache(self, key):
        raise Exception('Not implemented')

    # needs to return list of items
    def keys(self):
        raise Exception('Not implemented')

    def key_from_args(self, *args, **kwargs):
        stripped_kwargs = {k: v for k, v in kwargs.items() if k not in ['_precache', '_nocache', '_recache']}
        return self.keyfn(*args, **stripped_kwargs), stripped_kwargs

    #############################################################################
    # global cache functions

    def exists(self, *args, **kwargs):
        key, stripped_kwargs = self.key_from_args(*args, **kwargs)
        return self.exists_cache(key=key)

    def expired_items(self):
        for key in self.keys():
            cache = self.load_cache(key)
            diff = (datetime.datetime.utcnow() - cache['created']).total_seconds()
            if diff > self.timeout:
                yield cache

    def need_refresh_items(self):
        if not self.grace:
            return

        for key in self.keys():
            cache = self.load_cache(key)
            diff = (datetime.datetime.utcnow() - cache['created']).total_seconds()
            if self.timeout - self.grace < diff:
                yield cache

    def delete_all(self):
        for key in self.keys():
            self.delete_cache(key)

    def delete_expired(self):
        for cache in self.expired_items():
            if self.debug:
                logger.warn(
                "Deleting fn=%r, key=%r, args=%r, kwargs=%r",
                cache['key'], cache.get('args'), cache.get('kwargs')
            )
            self.delete_cache(key=cache['key'])

    def refresh_cache(self, fn):
        for cache in self.need_refresh_items():
            if self.debug:
                logger.warn(
                "Refreshing fn=%r, key=%r, args=%r, kwargs=%r",
                cache['key'], cache.get('args'), cache.get('kwargs')
            )
            fn(*cache['args'], **cache['kwargs'])

    def __call__(self, fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key, stripped_kwargs = self.key_from_args(*args, **kwargs)
            cachefnval = self.cachefn(*args, **kwargs) if self.cachefn else CACHE

            if self.debug:
                logger.warn("[cache - %r] CACHE fn=%r key=%r args=%r kwargs=%r stripped=%r", self.prefix, fn.__name__, key, args, kwargs, stripped_kwargs)

            if cachefnval == NOCACHE:
                if self.debug:
                    logger.warn("[cache - %r] NOCACHE fn=%r key=%r", self.prefix, fn.__name__, key)
                return fn(*args, **stripped_kwargs)

            if cachefnval == PRECACHE:
                if self.debug:
                    if self.debug:
                        logger.warn("[cache - %r] PRECACHE fn=%r key=%r", self.prefix, fn.__name__, key)
                cached = None
            else:
                cached = self.load_cache(key)

            diff = (datetime.datetime.utcnow() - cached['created']).total_seconds() if cached else 1e9

            do_cache = False
            if not cached:
                do_cache = True
                if self.debug:
                    logger.warn("[cache - %r] No cached value, creating cache fn=%r, key=%r", self.prefix, fn.__name__, key)
            elif diff > self.timeout:
                do_cache = True
                if self.debug:
                    logger.warn("[cache - %r] Timed out, creating cache fn=%r, key=%r, diff=%r", self.prefix, fn.__name__, key, diff)
            elif cachefnval == RECACHE and self.grace and self.timeout - self.grace < diff:
                do_cache = True
                if self.debug:
                    logger.warn("[cache - %r] RECACHE, re-creating cache fn=%r, key=%r diff=%r", self.prefix, fn.__name__, key, diff)

            if do_cache:
                val = fn(*args, **stripped_kwargs)
                cached = {
                    'key': key,
                    'created': datetime.datetime.utcnow(),
                    'value': bson.binary.Binary(bytes(val)) if self.binary else val,
                    'args': args,
                    'kwargs': stripped_kwargs,
                }
                self.update_cache(key, cached)

            return cached['value']

        return wrapper


class MemoryCache(CacheBase):
    def __init__(self, *args, **kwargs):
        super(MemoryCache, self).__init__(*args, **kwargs)
        self.data = {}

    def update_cache(self, key, cache):
        self.data[key] = cache

    def load_cache(self, key):
        return self.data.get(key)

    def exists_cache(self, key):
        return key in self.data

    def delete_cache(self, key):
        try:
            del self.data[key]
        except KeyError:
            pass

    def keys(self):
        return self.data.keys()


class FileCache(CacheBase):
    def __init__(self, basedir, *args, **kwargs):
        super(FileCache, self).__init__(*args, **kwargs)
        self.basedir = basedir

    def get_filename(self, key):
        key_pre = hashlib.md5(key).hexdigest()[:2]
        return os.path.join(self.basedir, self.prefix, key_pre, key)

    def update_cache(self, key, cache):
        file_name = self.get_filename(key)
        dir_name = os.path.dirname(file_name)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        with open(file_name, 'wb+') as f:
            json.dump(cache, f, cls=OurJSONEncoder)

    def load_cache(self, key):
        if not self.exists_cache(key):
            return None

        with open(self.get_filename(key), 'rb+') as f:
            v = json.load(f)
            v['created'] = dateutil.parser.parse(v['created'])
            return v

    def exists_cache(self, key):
        logger.warn("exists %r - %r - %r", key, self.get_filename(key), os.path.exists(self.get_filename(key)))
        return os.path.exists(self.get_filename(key))

    def delete_cache(self, key):
        try:
            os.unlink(self.get_filename(key))
        except KeyError:
            pass

    #def keys(self):
    #    return self.data.keys()


class PickleCache(CacheBase):
    def __init__(self, basedir, *args, **kwargs):
        super(PickleCache, self).__init__(*args, **kwargs)
        self.basedir = basedir

    def get_filename(self, key):
        key_pre = hashlib.md5(key).hexdigest()[:2]
        return os.path.join(self.basedir, self.prefix, key_pre, key)

    def update_cache(self, key, cache):
        file_name = self.get_filename(key)
        dir_name = os.path.dirname(file_name)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        with open(file_name, 'wb+') as f:
            pickle.dump(cache, f, pickle.HIGHEST_PROTOCOL)

    def load_cache(self, key):
        if not self.exists_cache(key):
            return None

        with open(self.get_filename(key), 'rb+') as f:
            v = pickle.load(f)
            return v

    def exists_cache(self, key):
        logger.warn("exists %r - %r - %r", key, self.get_filename(key), os.path.exists(self.get_filename(key)))
        return os.path.exists(self.get_filename(key))

    def delete_cache(self, key):
        try:
            os.unlink(self.get_filename(key))
        except KeyError:
            pass

    #def keys(self):
    #    return self.data.keys()



class MongoCache(CacheBase):
    def __init__(self, mongo, prefix, *args, **kwargs):
        super(MongoCache, self).__init__(prefix, *args, **kwargs)
        self.mongo_table = 'cache_' + prefix
        self.mongo = mongo

    def update_cache(self, key, cache):
        self.mongo.db[self.mongo_table].update({'key': key}, cache, upsert=True)

    def load_cache(self, key):
        return self.mongo.safedb[self.mongo_table].find_one({'key': key})

    def exists_cache(self, key):
        val = self.mongo.safedb[self.mongo_table].find_one({'key': key}, {'_id': 1})
        return val is not None

    def delete_cache(self, key):
        self.mongo.safedb[self.mongo_table].delete_one({'key': key})

    def keys(self):
        return (x['key'] for x in self.mongo.safedb[self.mongo_table].find({}, {'_id': 0, 'key': 1}))


class MysqlCache(CacheBase):
    def __init__(self, sql, prefix, *args, **kwargs):
        super(MysqlCache, self).__init__(prefix, *args, **kwargs)
        self.sql = sql
        self.prefix = prefix
        self.prefix_key = hashlib.md5(prefix).hexdigest()

    def _cache_key(self, key):
        return "{}:{}".format(self.prefix_key, key)

    def update_cache(self, key, cache):
        query = """
            insert into caches(cache_key, value, expiration) 
            values(%s, %s, %s) 
            on duplicate key update value=values(value), expiration=values(expiration)
        """
        expiration = datetime.datetime.utcnow() + datetime.timedelta(seconds=self.timeout)
        bindvars = [self._cache_key(key), json.dumps(cache, cls=OurJSONEncoder), expiration]
        self.sql.execute(query, bindvars)

    def load_cache(self, key):
        val = self.sql.select_0or1("select * from caches where cache_key=%s", [self._cache_key(key)])
        if val:
            v = json.loads(val.value)
            v['created'] = dateutil.parser.parse(v['created'])
            return v

        return None

    def exists_cache(self, key):
        return self.load_cache(key) is not None

    def delete_cache(self, key):
        self.sql.delete('caches', "cache_key=%s", [self._cache_key(key)])

    def keys(self):
        return list(self.sql.select_column("select cache_key from caches where cache_key like %s", [self.prefix_key + ":"]))

    @classmethod
    def add_migration(cls, migration_obj):
        migration_obj.add_statement("""
            create table caches(
                cache_key char(65) not null primary key,
                value mediumtext,
                expiration datetime
            )
        """)

    @classmethod
    def migration_delete_tables(cls):
        return ['caches']


class RedisCache(CacheBase):
    # connfn for otxp is redis_conn()
    def __init__(self, connfn, *args, **kwargs):
        super(RedisCache, self).__init__(*args, **kwargs)
        self.connfn = connfn

    def _conn(self):
        return self.connfn()

    def _key(self, keystr):
        return 'cache:{}:{}'.format(self.prefix, keystr)

    def update_cache(self, key, cache):
        key = self._key(key)
        value = json.dumps(cache, cls=OurJSONEncoder)
        if self.debug:
            logger.warn("redis update_cache key=%r, timeout=%r", key, self.timeout)
        with self._conn() as redis:
            redis.set(key, value, ex=self.timeout)

    def load_cache(self, key):
        with self._conn() as redis:
            val = redis.get(self._key(key))

        if val is not None:
            val = json.loads(val)
            val['created'] = dateutil.parser.parse(val['created'])

        if self.debug:
            logger.warn(
                "[cache - %r] redis load_cache key=%r, timeout=%r, exists=%r, created=%r",
                self.prefix, key, self.timeout, val is not None, val['created'] if val else None
            )
        return val

    def exists_cache(self, key):
        with self._conn() as redis:
            return redis.exists(self._key(key))

    def delete_cache(self, key):
        with self._conn() as redis:
            redis.delete(self._key(key))

    def keys(self):
        with self._conn() as redis:
            for key in redis.scan_iter(self._key('*')):
                yield ':'.join(key.split(':')[2:])



