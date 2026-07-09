import asyncio
import time
import httpx

CITIES = ["Kyiv", "Lviv", "Odesa", "Kharkiv", "Dnipro"]
BASE_URL = "http://localhost:8000/api/city"

async def fetch(client: httpx.AsyncClient, city: str):
    start = time.perf_counter()
    response = await client.get(f"{BASE_URL}/{city}")
    elapsed = time.perf_counter() - start
    print(f"{city:10s} -> {response.status_code} in {elapsed:.2f}s")
    return response

async def main():
    async with httpx.AsyncClient() as client:
        start = time.perf_counter()
        await asyncio.gather(*(fetch(client, city) for city in CITIES))
        total = time.perf_counter() - start
        print(f"\nTotal wall time for {len(CITIES)} requests: {total:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())