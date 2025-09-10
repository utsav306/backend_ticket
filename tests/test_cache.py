import pytest
import time
from app.cache.cache_utils import (
    set_cache, get_cache, delete_cache, clear_cache_pattern,
    make_events_cache_key, make_user_bookings_cache_key,
    invalidate_event_caches, invalidate_user_booking_cache
)

class TestCacheUtils:
    def test_set_and_get_cache(self):
        """Test basic cache set and get operations"""
        key = "test_key"
        value = {"test": "data", "number": 123}
        
        set_cache(key, value, ttl=60)
        cached_value = get_cache(key)
        
        assert cached_value == value
    
    def test_cache_expiry(self):
        """Test cache TTL expiry"""
        key = "test_expiry"
        value = "expiring_data"
        
        set_cache(key, value, ttl=1)  # 1 second TTL
        assert get_cache(key) == value
        
        time.sleep(2)  # Wait for expiry
        assert get_cache(key) is None
    
    def test_cache_delete(self):
        """Test cache deletion"""
        key = "test_delete"
        value = "delete_me"
        
        set_cache(key, value)
        assert get_cache(key) == value
        
        delete_cache(key)
        assert get_cache(key) is None
    
    def test_cache_key_generators(self):
        """Test cache key generation functions"""
        assert make_events_cache_key() == "events:all"
        assert make_user_bookings_cache_key(123) == "user:123:bookings"
    
    def test_cache_invalidation(self):
        """Test cache invalidation functions"""
        # Set some test caches
        set_cache("events:all", ["event1", "event2"])
        set_cache("user:123:bookings", ["booking1"])
        
        # Test invalidation
        invalidate_event_caches()
        invalidate_user_booking_cache(123)
        
        assert get_cache("events:all") is None
        assert get_cache("user:123:bookings") is None
