from locust import HttpUser, task, between
import random
import string
import time

class EventBookingStressTest(HttpUser):
    wait_time = between(0.1, 2)  # Wait 0.1-2 seconds between requests
    
    def on_start(self):
        """Setup before starting tests"""
        self.base_url = "http://127.0.0.1:8000"
        self.created_users = []
        self.created_events = []
        
        # Create some test users and events for realistic testing
        self.setup_test_data()
    
    def setup_test_data(self):
        """Create initial test data"""
        # Create test users
        for i in range(5):
            user_data = {
                "name": f"StressTest User {i}",
                "email": f"stress_user_{i}_{int(time.time())}@test.com",
                "password": "password123",
                "role": "user"
            }
            response = self.client.post("/users", json=user_data)
            if response.status_code == 200:
                self.created_users.append(response.json())
        
        # Create test events
        for i in range(3):
            event_data = {
                "name": f"Stress Test Event {i}",
                "venue": f"Test Venue {i}",
                "time": "2025-12-31T20:00:00",
                "capacity": 100
            }
            response = self.client.post("/events", json=event_data)
            if response.status_code == 200:
                self.created_events.append(response.json())

    @task(10)  # High frequency - test caching effectiveness
    def browse_events(self):
        """Test events browsing - should hit cache frequently"""
        response = self.client.get("/events")
        if response.status_code != 200:
            print(f"Events browse failed: {response.status_code}")

    @task(8)  # High frequency - test analytics caching
    def view_analytics(self):
        """Test analytics endpoint - should benefit from caching"""
        response = self.client.get("/admin/analytics")
        if response.status_code != 200:
            print(f"Analytics failed: {response.status_code}")

    @task(6)  # Medium frequency
    def check_health(self):
        """Test health endpoint"""
        self.client.get("/health")

    @task(5)  # Medium frequency
    def view_cache_status(self):
        """Test cache status endpoint"""
        self.client.get("/admin/cache/status")

    @task(4)  # Medium frequency
    def view_user_bookings(self):
        """Test user bookings - should hit cache after first request"""
        if self.created_users:
            user = random.choice(self.created_users)
            response = self.client.get(f"/users/{user['id']}/bookings")
            if response.status_code != 200:
                print(f"User bookings failed: {response.status_code}")

    @task(3)  # Lower frequency - writes that invalidate cache
    def book_event(self):
        """Test event booking - invalidates caches"""
        if self.created_users and self.created_events:
            user = random.choice(self.created_users)
            event = random.choice(self.created_events)
            
            booking_data = {"user_id": user["id"]}
            response = self.client.post(f"/events/{event['id']}/book", json=booking_data)
            # Don't assert here as event might be full

    @task(2)  # Lower frequency
    def create_user(self):
        """Test user creation"""
        random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        user_data = {
            "name": f"Load Test User {random_id}",
            "email": f"load_test_{random_id}@example.com",
            "password": "password123",
            "role": "user"
        }
        response = self.client.post("/users", json=user_data)
        if response.status_code == 200:
            self.created_users.append(response.json())

    @task(1)  # Lowest frequency - cache invalidation
    def clear_cache(self):
        """Test cache clearing - occasional cache management"""
        self.client.delete("/admin/cache/events")


class CacheStressTest(HttpUser):
    """Focused cache stress testing"""
    wait_time = between(0.05, 0.5)  # Very fast requests to stress cache
    
    @task(20)
    def rapid_events_access(self):
        """Rapid events access to test cache performance"""
        self.client.get("/events")
    
    @task(15)
    def rapid_analytics_access(self):
        """Rapid analytics access to test cache performance"""
        self.client.get("/admin/analytics")
    
    @task(10)
    def cache_status_check(self):
        """Check cache status frequently"""
        self.client.get("/admin/cache/status")

    @task(5)
    def health_check_spam(self):
        """Spam health checks"""
        self.client.get("/health")


class DatabaseStressTest(HttpUser):
    """Test database operations and cache invalidation"""
    wait_time = between(0.2, 1)
    
    @task(8)
    def create_events(self):
        """Create events - tests cache invalidation"""
        random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        event_data = {
            "name": f"DB Stress Event {random_id}",
            "venue": f"Venue {random_id}",
            "time": "2025-12-31T19:00:00",
            "capacity": random.randint(50, 200)
        }
        self.client.post("/events", json=event_data)
    
    @task(6)
    def read_events_after_write(self):
        """Read events after writes to test cache refresh"""
        self.client.get("/events")
    
    @task(4)
    def analytics_after_changes(self):
        """Get analytics after data changes"""
        self.client.get("/admin/analytics")
