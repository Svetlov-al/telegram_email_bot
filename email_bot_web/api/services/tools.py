import json
import os
from functools import wraps

from redis.asyncio import Redis as redis


class RedisTools:

    def __init__(self):
        self.redis_host = os.environ.get('REDIS_HOST', 'localhost')
        self.redis_port = os.environ.get('REDIS_PORT', 6379)
        self.redis_url = f'redis://{self.redis_host}:{self.redis_port}/'
        self.redis = redis.from_url(self.redis_url)

    async def get_key(self, key: str) -> str:
        value = await self.redis.get(key)
        return value.decode('utf-8') if value else None

    async def set_key(self, key: str, value: str, expire_time: int | None = None):
        if expire_time:
            await self.redis.setex(key, expire_time, value.encode('utf-8'))
        else:
            await self.redis.set(key, value.encode('utf-8'))

    async def get_list(self, key: str) -> list:
        values = await self.redis.lrange(key, 0, -1)
        return [v.decode('utf-8') for v in values]

    async def add_to_list(self, key: str, value: str, expire_time: int | None = None):
        await self.redis.rpush(key, value)
        if expire_time:
            await self.redis.expire(key, expire_time)

    async def delete_key(self, key: str):
        await self.redis.delete(key)

    async def clear_all(self):
        await self.redis.flushall()


def cache_async(key_prefix: str, expiration: int = 3600, schema=None):
    """Асинхронный декоратор
    Принимает ключ, время инвалидации, pydantic схему"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Создаем словарь из позиционных и именованных аргументов
            all_args = {**kwargs}
            for i, arg in enumerate(args):
                all_args[func.__code__.co_varnames[i]] = arg

            # Формируем ключ, заменяя плейсхолдеры на реальные значения аргументов
            key = key_prefix.format(**all_args)

            cached_data_str = await redis_client.get_key(key)
            if cached_data_str:
                cached_data = json.loads(cached_data_str)
                if schema:
                    if isinstance(cached_data, list):
                        return [schema(**item) for item in cached_data]
                    return schema(**cached_data)
                return cached_data

            result = await func(*args, **kwargs)
            if isinstance(result, list):
                serialized_result = [item.dict() if hasattr(item, 'dict') else item for item in result]
            else:
                serialized_result = result.dict() if hasattr(result, 'dict') else result
            await redis_client.set_key(key, json.dumps(serialized_result), expiration)
            return result

        return wrapper

    return decorator


redis_client = RedisTools()
