from fastapi import APIRouter, Request
import service
from decorators import rate_limit, cache_responce

router = APIRouter()

@router.get("/")
@rate_limit(max_requests=10, window_seconds=60)
@cache_responce(ttl=service.month_in_seconds, prefix="health_check")
async def helth_check(request: Request) -> dict:
    return {"message": "successful"}

@router.get("/api/city/{city_name}")
@rate_limit(max_requests=10, window_seconds=60)
async def get_weather(request: Request, city_name: str) -> dict:
    data = await service.get_city_weather(city_name=city_name)
    return data
    