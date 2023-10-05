import json
from functools import wraps

from django.core.cache import cache

CACHE_PREFIX = 'decorator_cache:'


class RedisTools:

    @staticmethod
    def get_key(key: str) -> str:
        """Получение занчения по ключу"""
        value = cache.get(key)
        return value if value else None

    @staticmethod
    def set_key(key: str, value: str, expire_time: int | None = None) -> None:
        """Установка значения по ключу"""
        cache.set(key, value, expire_time)

    @staticmethod
    def delete_key(key: str) -> None:
        """Удаление значения по ключу"""
        cache.delete(key)

    @staticmethod
    def clear_decorator_cache() -> None:
        """Метод очищения кеша связанного с декоратором"""
        cache_prefix = CACHE_PREFIX
        all_keys = cache.keys(cache_prefix + '*')
        for key in all_keys:
            cache.delete(key)


def cache_async(key_prefix='', schema=None, use_cache=True, expiration=3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            redis_tools = RedisTools()

            # Создаем словарь из позиционных и именованных аргументов
            all_args = {**kwargs}
            for i, arg in enumerate(args):
                all_args[func.__code__.co_varnames[i]] = arg

            # Формируем ключ, заменяя плейсхолдеры на реальные значения аргументов
            key = CACHE_PREFIX + key_prefix.format(**all_args)

            if use_cache:
                cached_data_str = redis_tools.get_key(key)  # используем ваш метод get_key
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
                redis_tools.set_key(key, json.dumps(serialized_result),
                                    expiration)
            return result

        return wrapper

    return decorator


redis_client = RedisTools()
