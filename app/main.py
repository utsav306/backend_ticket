from fastapi import FastAPI
from app.routers import users, admin, events, bookings, waitlist
from app.cache.redis_client import redis_client

app = FastAPI(title="Event Booking API", description="Event booking system with Redis caching")

app.include_router(users.router)
app.include_router(admin.router)
app.include_router(events.router)
app.include_router(bookings.router)
app.include_router(waitlist.router)

@app.get("/")
def root():
    return {"message": "Event Booking API", "cache_status": "Redis Connected" if redis_client else "In-Memory Cache"}

@app.get("/health")
def health_check():
    cache_status = "connected" if redis_client else "fallback"
    return {
        "status": "healthy",
        "cache": cache_status,
        "redis_available": redis_client is not None
    }
