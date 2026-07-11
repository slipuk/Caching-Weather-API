# Weather API

A small FastAPI service that returns current weather for a city name. It sits in front of the [OpenWeatherMap](https://openweathermap.org/api) API, caches results in Redis to cut down on external calls, and rate-limits clients per IP.

## Project URL

https://roadmap.sh/projects/weather-api-wrapper-service

## Features

- **City weather lookup** — resolves a city name to coordinates, then fetches current weather.
- **Two-layer caching (Redis)**
  - Geocoding results (city → coordinates) are cached for 30 days, since a city's coordinates essentially never change.
  - Weather results are cached for 10 minutes, since weather changes often.
  - This means a cache miss after the weather TTL expires but within the 30-day coordinate window costs **one** external API call instead of two.
- **Per-IP rate limiting** — a fixed-window limiter (default: 10 requests / 60 seconds per client IP) backed by Redis, returning `429 Too Many Requests` once exceeded.
- **Fully async** — uses `httpx.AsyncClient` and `redis.asyncio` throughout, so a slow upstream call doesn't block the event loop for other clients.

## Architecture

```
Client
  │
  ▼
FastAPI route (routes.py)
  │  ┌────────────────────┐
  ├─▶│ rate_limit decorator │  → 429 if IP exceeded quota
  │  └────────────────────┘
  ▼
service.get_city_weather()
  │  ┌────────────────────┐
  ├─▶│ cache_response decorator │  → return cached JSON if present
  │  └────────────────────┘
  ▼
service.get_city_coordinates()  (also cached, 30-day TTL)
  │
  ▼
OpenWeatherMap Geocoding API → OpenWeatherMap Weather API
```

### Project structure

```bash
└── Caching-Weather-API/
    ├── app/
    │   ├── main.py               # FastAPI app entrypoint
    │   ├── routes.py             # API routes
    │   ├── service.py            # OpenWeatherMap integration (geocoding + weather)
    │   └── decorators.py         # cache_response and rate_limit decorators, Redis client
    ├── tests/
    │   ├── test_concurency.py    # fires concurrent requests to check caching / async behavior
    │   └── test_ratelimit.py     # fires repeated requests to check rate limiting
    ├── README.md
    ├── requirements.txt
    ├── .env
    └── .gitignore
```

## How caching works

`cache_response(ttl, prefix)` in `decorators.py` wraps an async function. On each call it:
1. Builds a Redis key from `prefix`, the function name, and the call arguments (hashed with SHA-256).
2. Returns the cached JSON value from Redis if the key exists (cache hit — no external call is made).
3. Otherwise calls the wrapped function, stores its result in Redis with the given `ttl`, and returns it (cache miss).

Only non-`None` results are cached, so failed lookups (e.g. an unknown city) aren't cached and don't get stuck serving an error to everyone for the TTL duration.

## How rate limiting works

`rate_limit(max_requests, window_seconds)` in `decorators.py` wraps an async route. On each call it:
1. Builds a Redis key from the client's IP and the route name.
2. Atomically increments a counter for that key (`INCR`).
3. On the first request in a window, sets the key to expire after `window_seconds` (`EXPIRE`) — this is what resets the counter.
4. If the counter exceeds `max_requests` before the window expires, raises `HTTPException(429)` with the number of seconds remaining until the window resets.

## API Reference

### `GET /`

Health check.

**Response `200`**
```json
{ "message": "successful" }
```

### `GET /api/city/{city_name}`

Returns current weather for the given city.

**Path parameters**

| Name        | Type   | Description                          |
|-------------|--------|---------------------------------------|
| `city_name` | string | Name of the city, e.g. `Kyiv`, `Lviv` |

**Response `200`** (success)
```json
{
  "coord": { "lon": 30.5238, "lat": 50.4547 },
  "weather": [ { "main": "Clouds", "description": "overcast clouds" } ],
  "main": { "temp": 21.3, "feels_like": 20.9, "humidity": 60 },
  "name": "Kyiv"
}
```
Full response shape matches [OpenWeatherMap's Current Weather API](https://openweathermap.org/current).

**Response `200`** (city not found — OpenWeatherMap's geocoding quirk returns `200` with an empty result rather than `404`)
```json
{ "error": "Could not fetch weather for 'Atlantis'" }
```

**Response `429`** (rate limit exceeded)
```json
{ "detail": "Too many requests. Try again in 42 seconds." }
```

## Installation

### Prerequisites

- Python 3.10+
- [Redis](https://redis.io/docs/install/install-redis/) running locally (default: `localhost:6379`)
- An [OpenWeatherMap API key](https://home.openweathermap.org/users/sign_up) (free tier is sufficient)

### Setup

1. **Clone the repository and enter the project folder**
   ```bash
   git clone <your-repo-url>
   cd <project-folder>
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:
   ```env
   OpenWeatherMap_API_key=your_api_key_here
   ```

5. **Start Redis** (if not already running)
   ```bash
   redis-server
   ```
   Verify it's up:
   ```bash
   redis-cli ping
   # should return: PONG
   ```

6. **Run the API**
   ```bash
   uvicorn main:app --reload
   ```
   The API will be available at `http://localhost:8000`.

### Try it out

```bash
curl http://localhost:8000/api/city/Kyiv
```

## Testing

Two standalone scripts are included for manual verification (not a formal test suite):

- **`test_concurency.py`** — fires 5 concurrent requests for different cities and prints per-request timing plus total wall time. Useful for confirming requests aren't being serialized and that caching is reducing response time on repeat calls.
  ```bash
  python test_concurency.py
  ```

- **`test_ratelimit.py`** — repeatedly requests the same city every 0.5s in a loop to confirm the rate limiter kicks in with `429` once the quota is exceeded. Stop with `Ctrl+C`.
  ```bash
  python test_ratelimit.py
  ```

## Inspecting Redis directly

```bash
redis-cli KEYS "weather:*"      # cached weather results
redis-cli KEYS "coords:*"       # cached coordinate lookups
redis-cli KEYS "ratelimit:*"    # active rate-limit counters
redis-cli TTL <key>             # seconds remaining before a key expires
redis-cli FLUSHALL              # clear all cached/rate-limit data (dev only)
```

## Known limitations

- Rate limiting and caching share the same Redis instance/database with no key-space separation beyond prefixes — fine for a single-service setup, worth revisiting if this ever runs alongside other apps on the same Redis.
- Rate limiting is keyed by IP only; clients behind a shared IP (NAT, corporate network) share a quota.
- No authentication — the API is fully open. Add an API-key layer before deploying publicly.
