import json
import os
from functools import wraps
from typing import Any

import redis
from django.core.cache import cache
from email_service.logger_config import logger

CACHE_PREFIX = 'decorator_cache:'


class RedisTools:

    async def get_key(self, key: str) -> str:
        """Получение занчения по ключу"""
        value = cache.get(key)
        return value if value else None

    async def set_key(self, key: str, value: str, expire_time: int | None = None) -> None:
        """Установка значения по ключу"""
        cache.set(key, value, expire_time)

    async def delete_key(self, key: str) -> None:
        """Удаление значения по ключу"""
        cache.delete(key)

    async def clear_decorator_cache(self) -> None:
        cache_prefix = CACHE_PREFIX
        keys = cache.keys(cache_prefix + '*')
        for key in keys:
            cache.delete(key)


def cache_async(key_prefix: str, expiration: int = 3600, schema=None, use_cache=True):
    """Асинхронный декоратор:
    Принимает ключ,
    Время инвалидации,
    Pydantic схему
    Флаг кеширования"""
    cache_prefix = CACHE_PREFIX

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Создаем словарь из позиционных и именованных аргументов
            all_args = {**kwargs}
            for i, arg in enumerate(args):
                all_args[func.__code__.co_varnames[i]] = arg

            # Формируем ключ, заменяя плейсхолдеры на реальные значения аргументов
            key = cache_prefix + key_prefix.format(**all_args)

            if use_cache:
                cached_data_str = cache.get(key)
                if cached_data_str:
                    cached_data = json.loads(cached_data_str)
                    if schema:
                        if isinstance(cached_data, list):
                            return [schema(**item) for item in cached_data]
                        return schema(**cached_data)
                    return cached_data

            result = await func(*args, **kwargs)
            if use_cache:
                if isinstance(result, list):
                    serialized_result = [item.dict() if hasattr(item, 'dict') else item for item in result]
                else:
                    serialized_result = result.dict() if hasattr(result, 'dict') else result
                cache.set(key, json.dumps(serialized_result), expiration)
            return result

        return wrapper

    return decorator


def add_prefix_to_key(base_key: str) -> str:
    return f':1:{base_key}'


class SyncRedisTools:

    def __init__(self):
        self.redis_host = os.environ.get('REDIS_HOST', 'localhost')
        self.redis_port = os.environ.get('REDIS_PORT', 6379)
        self.redis_url = f'redis://{self.redis_host}:{self.redis_port}/'
        self.redis = redis.from_url(self.redis_url)

    def sync_get_key(self, key: str) -> str | None:
        """Синхронное получение ключей"""
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value.decode('utf-8'))
            return None
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f'Error getting key {key}: {e}')
            return None

    def sync_set_key(self, key: str, value: Any, expire_time: int | None = None):
        """Синхронная установка ключей"""
        serialized_value = json.dumps(value).encode('utf-8')
        try:
            if expire_time:
                self.redis.setex(key, expire_time, serialized_value)
            else:
                self.redis.set(key, serialized_value)
        except redis.RedisError as e:
            logger.error(f'Error setting key {key}: {e}')


redis_client = RedisTools()

sync_redis_client = SyncRedisTools()
