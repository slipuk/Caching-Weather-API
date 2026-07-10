import httpx
import dotenv
import os
from decorators import cache_responce

dotenv.load_dotenv()

OpenWeatherMap_API_key = os.getenv("OpenWeatherMap_API_key")
# 60 sec * 60 min * 24h * 30 days
# city coordinates never change 
month_in_seconds = 60 * 60 * 24 * 30

@cache_responce(ttl=month_in_seconds, prefix="coords")
async def get_city_coordinates(city_name: str): 
    """Function to get city coordinates just by name
    It returns most probable answer based on population of the city"""

    # example url
    # http://api.openweathermap.org/geo/1.0/direct?q={city name},{state code},{country code}&limit={limit}&appid={API key}

    geocoding_api_url = "http://api.openweathermap.org/geo/1.0/direct"
    geocoding_api_params = {
        "q": city_name,
        "limit": 1,
        "appid": OpenWeatherMap_API_key
    }
    async with httpx.AsyncClient() as client:
        responce = await client.get(url=geocoding_api_url, params=geocoding_api_params)

    if responce.status_code == 200 and responce.json():
        data = responce.json()
        return {
            "lat": data[0]["lat"],
            "lon": data[0]["lon"]
        }
    else:
        return None
    
@cache_responce(ttl=600, prefix="weather")
async def get_city_weather(city_name: str):
    "Function to get city weather using get_city_coordinates function"

    # example url
    # https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API key}

    city_coordinates = await get_city_coordinates(city_name=city_name)
    if not city_coordinates:
        return None

    weather_api_url = "https://api.openweathermap.org/data/2.5/weather"
    weather_api_params = {
        "lat": city_coordinates["lat"], 
        "lon": city_coordinates["lon"], 
        "appid": OpenWeatherMap_API_key,
        "units": "metric"
    }
    async with httpx.AsyncClient() as client:
        responce = await client.get(url=weather_api_url, params=weather_api_params)

    if responce.status_code == 200:
        data = responce.json()
        return data
    else:
        return None