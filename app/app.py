from fastapi import FastAPI
import redis
from routes import router

app = FastAPI()

app.include_router(router=router)

redis_client = redis.Redis(host="localhost", port=6379, db=0)