import json
import hashlib
import functools
import redis.asyncio as redis

redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

def cache_responce(ttl: int = 300, prefix: str = "cache"):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key_source = f"{prefix}:{func.__name__}:{args}:{kwargs.items()}"
            cache_key = hashlib.sha256(key_source.encode()).hexdigest()

            cached = await redis_client.get(cache_key)
            if cached is not None:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)

            if result is not None:
                await redis_client.set(cache_key, json.dumps(result), ex=ttl)
            return result
        return wrapper
    return decorator