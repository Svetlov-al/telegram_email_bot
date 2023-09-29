import os

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


redis_client = RedisTools()
