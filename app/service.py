import requests
import dotenv
import os

dotenv.load_dotenv()

OpenWeatherMap_API_key = os.getenv("OpenWeatherMap_API_key")

def get_city_coordinates(city_name: str) -> dict:
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

    responce = requests.get(geocoding_api_url, geocoding_api_params)

    if responce.status_code == 200 and responce.json():
        data = responce.json()
        return {
            "lat": data[0]["lat"],
            "lon": data[0]["lon"]
        }, responce.status_code
    else:
        return [], responce.status_code
    
def get_city_weather(city_name: str) -> dict:
    "Function to get city weather using get_city_coordinates function"

    # example url
    # https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API key}

    city_coordinates, status_code = get_city_coordinates(city_name=city_name)
    if status_code != 200 or not city_coordinates:
        return f"Error {status_code}", status_code

    weather_api_url = "https://api.openweathermap.org/data/2.5/weather"
    weather_api_params = {
        "lat": city_coordinates["lat"],
        "lon": city_coordinates["lon"],
        "appid": OpenWeatherMap_API_key,
        "units": "metric"
    }

    responce = requests.get(weather_api_url, weather_api_params)

    if responce.status_code == 200:
        data = responce.json()
        return data, responce.status_code
    else:
        return f"Error {responce.status_code}", responce.status_code