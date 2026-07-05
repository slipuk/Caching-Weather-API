from fastapi import APIRouter
import service

router = APIRouter()

@router.get("/")
async def helth_check():
    return {"message": "successful"}

@router.get("/api/city/{city_name}")
async def get_weather(city_name):
    data, status_code = service.get_city_weather(city_name=city_name)
    if status_code != 200:
        return f"Error {status_code}"
    return data