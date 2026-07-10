import json
import hashlib
import functools
import redis.asyncio as redis
from fastapi import Request, HTTPException

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

def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            client_ip = request.client.host
            ratelimit_key = f"ratelimit:{client_ip}:{func.__name__}"

            current = await redis_client.incr(ratelimit_key)

            if current == 1:
                await redis_client.expire(ratelimit_key, window_seconds)

            if current > max_requests:
                ttl = redis_client.ttl(ratelimit_key)
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many requests. Try again in {ttl} seconds."
                )
            result = await func(request, *args, **kwargs) 
            return result
        return wrapper
    return decorator
