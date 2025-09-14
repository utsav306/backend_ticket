import redis
import os

REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL:
    try:
        redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        redis_client.ping()
        print("✅ Redis connected via URL")
    except Exception as e:
        redis_client = None
        print("⚠️ Redis not available, falling back to in-memory cache:", e)
else:
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
        )
        redis_client.ping()
        print("✅ Redis connected via host/port")
    except Exception as e:
        redis_client = None
        print("⚠️ Redis not available, falling back to in-memory cache:", e)
