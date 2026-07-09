from fastapi import APIRouter
import service
from decorators import cache_responce

router = APIRouter()

@router.get("/")
async def helth_check():
    return {"message": "successful"}

@router.get("/api/city/{city_name}")
@cache_responce(tt1=600, prefix="weather")
async def get_weather(city_name: str):
    data = service.get_city_weather(city_name=city_name)
    if not data:
        return {
            "error": f"Could not fetch weather for '{city_name}'"
        }
    return data
    