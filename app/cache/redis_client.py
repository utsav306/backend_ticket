import os

try:
    from upstash_redis import Redis as UpstashRedis
    UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
    UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_TOKEN")
    if UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN:
        redis_client = UpstashRedis(url=UPSTASH_REDIS_URL, token=UPSTASH_REDIS_TOKEN)
        # Test connection
        redis_client.set("__healthcheck__", "ok")
        print("✅ Upstash Redis connected")
    else:
        import redis
        REDIS_URL = os.getenv("REDIS_URL")
        if REDIS_URL:
            redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
            redis_client.ping()
            print("✅ Redis connected via URL")
        else:
            REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
            REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
            REDIS_DB = int(os.getenv("REDIS_DB", 0))
            redis_client = redis.Redis(
                host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
            )
            redis_client.ping()
            print("✅ Redis connected via host/port")
except Exception as e:
    redis_client = None
    print("⚠️ Redis not available, falling back to in-memory cache:", e)
