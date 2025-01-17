import functools
import logging

from django.conf import settings
from django.core.cache.backends.base import BaseCache
from django.utils.module_loading import import_string

from .exceptions import ConnectionInterrupted

DJANGO_REDIS_IGNORE_EXCEPTIONS = getattr(settings, "DJANGO_REDIS_IGNORE_EXCEPTIONS", False)
DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS = getattr(settings, "DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS", False)
DJANGO_REDIS_LOGGER = getattr(settings, "DJANGO_REDIS_LOGGER", False)
DJANGO_REDIS_SCAN_ITERSIZE = getattr(settings, "DJANGO_REDIS_SCAN_ITERSIZE", 10)


if DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS:
    logger = logging.getLogger(DJANGO_REDIS_LOGGER or __name__)


def omit_exception(method=None, return_value=None):
    """
    Simple decorator that intercepts connection
    errors and ignores these if settings specify this.
    """

    if method is None:
        return functools.partial(omit_exception, return_value=return_value)

    @functools.wraps(method)
    def _decorator(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except ConnectionInterrupted as e:
            if self._ignore_exceptions:
                if DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS:
                    logger.error(str(e))

                return return_value
            raise e.parent
    return _decorator


class RedisCache(BaseCache):
    """Redis 缓存类

    该类的实例叫做「缓存对象」，该对象的 client 属性值就是「Redis 客户端对象」
    调用「缓存对象」的各种方法就等同于调用「Redis 客户端对象」的各种方法
    """

    def __init__(self, server, params):
        # 参数 server 是 Redis 服务器的 IP 地址或连接串
        super().__init__(params)
        self._server = server
        self._params = params

        options = params.get("OPTIONS", {})
        self._client_cls = options.get("CLIENT_CLASS", "django_redis.client.DefaultClient")
        self._client_cls = import_string(self._client_cls)
        self._client = None

        self._ignore_exceptions = options.get("IGNORE_EXCEPTIONS", DJANGO_REDIS_IGNORE_EXCEPTIONS)
        # 下面这行是为了分析源码写的，本不存在
        self.client

    @property
    def client(self):
        """该属性值是「Redis 客户端对象」
        """
        if self._client is None:
            # 下面这个属性值通常是 django_redis.client.default.DefaultClient 类的实例
            self._client = self._client_cls(self._server, self._params, self)
        return self._client

    @omit_exception
    def set(self, *args, **kwargs):
        return self.client.set(*args, **kwargs)

    @omit_exception
    def incr_version(self, *args, **kwargs):
        return self.client.incr_version(*args, **kwargs)

    @omit_exception
    def add(self, *args, **kwargs):
        return self.client.add(*args, **kwargs)

    @omit_exception
    def get(self, key, default=None, version=None, client=None):
        try:
            return self.client.get(key, default=default, version=version,
                                   client=client)
        except ConnectionInterrupted as e:
            if self._ignore_exceptions:
                if DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS:
                    logger.error(str(e))
                return default
            raise

    @omit_exception
    def delete(self, *args, **kwargs):
        return self.client.delete(*args, **kwargs)

    @omit_exception
    def delete_pattern(self, *args, **kwargs):
        kwargs['itersize'] = kwargs.get('itersize', DJANGO_REDIS_SCAN_ITERSIZE)
        return self.client.delete_pattern(*args, **kwargs)

    @omit_exception
    def delete_many(self, *args, **kwargs):
        return self.client.delete_many(*args, **kwargs)

    @omit_exception
    def clear(self):
        return self.client.clear()

    @omit_exception(return_value={})
    def get_many(self, *args, **kwargs):
        return self.client.get_many(*args, **kwargs)

    @omit_exception
    def set_many(self, *args, **kwargs):
        return self.client.set_many(*args, **kwargs)

    @omit_exception
    def incr(self, *args, **kwargs):
        return self.client.incr(*args, **kwargs)

    @omit_exception
    def decr(self, *args, **kwargs):
        return self.client.decr(*args, **kwargs)

    @omit_exception
    def has_key(self, *args, **kwargs):
        return self.client.has_key(*args, **kwargs)

    @omit_exception
    def keys(self, *args, **kwargs):
        return self.client.keys(*args, **kwargs)

    @omit_exception
    def iter_keys(self, *args, **kwargs):
        return self.client.iter_keys(*args, **kwargs)

    @omit_exception
    def ttl(self, *args, **kwargs):
        return self.client.ttl(*args, **kwargs)

    @omit_exception
    def persist(self, *args, **kwargs):
        return self.client.persist(*args, **kwargs)

    @omit_exception
    def expire(self, *args, **kwargs):
        return self.client.expire(*args, **kwargs)

    @omit_exception
    def lock(self, *args, **kwargs):
        return self.client.lock(*args, **kwargs)

    @omit_exception
    def close(self, **kwargs):
        self.client.close(**kwargs)

    @omit_exception
    def touch(self, key, timeout=None, version=None):
        return self.client.touch(key, timeout=timeout, version=version)
