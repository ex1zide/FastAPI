import aioredis
from fastapi import Request, Response
from fastapi.concurrency import run_in_threadpool
from functools import wraps
import pickle
import json
from typing import Optional, Any, Callable, List
import hashlib
import os

class RedisCache:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None

    async def init_redis(self):
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        return self

    async def close(self):
        if self.redis:
            await self.redis.close()

    def cache(
        self,
        key_prefix: str = "",
        ttl: int = 300,
        ignore_args: List[str] = None,
        serializer: str = "pickle"
    ):
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.redis:
                    await self.init_redis()

                cache_kwargs = kwargs.copy()
                if ignore_args:
                    for arg in ignore_args:
                        cache_kwargs.pop(arg, None)

                cache_key = f"{key_prefix}:{func.__name__}:{hashlib.md5(json.dumps(cache_kwargs, sort_keys=True).encode()).hexdigest()}"

                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    if serializer == "json":
                        return json.loads(cached_data)
                    return pickle.loads(cached_data.encode())

                result = await func(*args, **kwargs)

                if result is not None:
                    if serializer == "json":
                        # Сериализуем объекты SQLModel в JSON
                        if hasattr(result, '__iter__') and not isinstance(result, str):
                            json_data = json.dumps([item.dict() if hasattr(item, 'dict') else item for item in result])
                        else:
                            json_data = json.dumps(result.dict() if hasattr(result, 'dict') else result)
                        await self.redis.setex(cache_key, ttl, json_data)
                    else:
                        await self.redis.setex(cache_key, ttl, pickle.dumps(result))

                return result
            return wrapper
        return decorator
    
    async def invalidate_by_prefix(self, prefix: str):
        if not self.redis:
            await self.init_redis()

        keys = []
        async for key in self.redis.scan_iter(f"{prefix}:*"):
            keys.append(key)
        
        if keys:
            await self.redis.delete(*keys)

redis_cache = RedisCache()