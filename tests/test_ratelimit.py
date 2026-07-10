import requests
import time

base_url = "http://0.0.0.0:8000/api/city/"
cities = ["Kyiv"]

while True:
    for city in cities:
        response = requests.get(url=f"{base_url + city}")
        if response.status_code == 200:
            print(f"Request to {base_url+city} successful")
        else:
            print(response.status_code)
        time.sleep(0.5)