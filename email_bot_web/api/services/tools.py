import os

import redis


class RedisTools:

    def __init__(self):
        redis_host = os.environ.get('REDIS_HOST', 'localhost')
        redis_port = os.environ.get('REDIS_PORT', 6379)
        redis_url = f'redis://{redis_host}:{redis_port}/'
        self.redis = redis.from_url(redis_url)

    def get_key(self, key: str) -> str:
        value = self.redis.get(key)
        return value.decode('utf-8') if value else None

    def set_key(self, key: str, value: str, expire_time: int | None = None):
        if expire_time:
            self.redis.setex(key, expire_time, value.encode('utf-8'))
        else:
            self.redis.set(key, value.encode('utf-8'))

    def get_list(self, key: str) -> list:
        values = self.redis.lrange(key, 0, -1)
        return [v.decode('utf-8') for v in values]

    def add_to_list(self, key: str, value: str, expire_time: int | None = None):
        self.redis.rpush(key, value)
        if expire_time:
            self.redis.expire(key, expire_time)

    def delete_key(self, key: str):
        self.redis.delete(key)

    def clear_all(self):
        self.redis.flushall()


redis_client = RedisTools()
