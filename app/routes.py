from fastapi import APIRouter, Request
import service
from decorators import rate_limit

router = APIRouter()

@router.get("/")
async def helth_check() -> dict:
    return {"message": "successful"}

@router.get("/api/city/{city_name}")
@rate_limit(max_requests=10, window_seconds=60)
async def get_weather(request: Request, city_name: str) -> dict:
    data = await service.get_city_weather(city_name=city_name)
    if not data:
        return {
            "error": f"Could not fetch weather for '{city_name}'"
        }
    return data
    