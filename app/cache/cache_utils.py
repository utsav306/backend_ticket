
import time
import json
from typing import Any, Optional, List
from app.cache.redis_client import redis_client

# In-memory fallback
_memory_cache = {}

def set_cache(key: str, value: Any, ttl: int = 60):
    """Set cache with TTL (time to live) in seconds"""
    if redis_client:
        redis_client.setex(key, ttl, json.dumps(value, default=str))
    else:
        _memory_cache[key] = {"value": value, "expiry": time.time() + ttl}

def get_cache(key: str) -> Optional[Any]:
    """Get cached value by key"""
    if redis_client:
        cached = redis_client.get(key)
        return json.loads(cached) if cached else None
    else:
        data = _memory_cache.get(key)
        if data and data["expiry"] > time.time():
            return data["value"]
        elif data:
            del _memory_cache[key]
        return None

def delete_cache(key: str):
    """Delete cached value by key"""
    if redis_client:
        redis_client.delete(key)
    else:
        _memory_cache.pop(key, None)

def clear_cache_pattern(pattern: str):
    """Clear all cache keys matching pattern"""
    if redis_client:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    else:
        # For memory cache, simple prefix matching
        keys_to_delete = [k for k in _memory_cache.keys() if k.startswith(pattern.replace('*', ''))]
        for key in keys_to_delete:
            del _memory_cache[key]

# Cache key generators
def make_events_cache_key() -> str:
    """Generate cache key for all events"""
    return "events:all"

def make_event_cache_key(event_id: int) -> str:
    """Generate cache key for specific event"""
    return f"event:{event_id}"

def make_user_bookings_cache_key(user_id: int) -> str:
    """Generate cache key for user bookings"""
    return f"user:{user_id}:bookings"

def make_analytics_cache_key() -> str:
    """Generate cache key for analytics data"""
    return "analytics:data"

# Cache invalidation helpers
def invalidate_event_caches(event_id: int = None):
    """Invalidate event-related caches"""
    delete_cache(make_events_cache_key())
    delete_cache(make_analytics_cache_key())
    if event_id:
        delete_cache(make_event_cache_key(event_id))

def invalidate_user_booking_cache(user_id: int):
    """Invalidate user booking cache"""
    delete_cache(make_user_bookings_cache_key(user_id))
