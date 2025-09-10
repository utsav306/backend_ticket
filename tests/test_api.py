import pytest
import httpx
import asyncio
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAPIEndpoints:
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "cache_status" in data
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "cache" in data
        assert "redis_available" in data
    
    def test_events_endpoint_caching(self):
        """Test events endpoint caching behavior"""
        # First request - should hit database
        response1 = client.get("/events")
        assert response1.status_code == 200
        
        # Second request - should hit cache
        response2 = client.get("/events")
        assert response2.status_code == 200
        assert response1.json() == response2.json()
    
    def test_cache_status_endpoint(self):
        """Test cache status endpoint"""
        response = client.get("/admin/cache/status")
        assert response.status_code == 200
        data = response.json()
        assert "cache_type" in data
        assert "status" in data
    
    def test_cache_clear_endpoint(self):
        """Test cache clearing"""
        # Clear cache
        response = client.delete("/admin/cache/clear")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_user_creation(self):
        """Test user creation endpoint"""
        user_data = {
            "name": "Test User",
            "email": f"test_{int(asyncio.get_event_loop().time())}@example.com",
            "password": "testpass123",
            "role": "user"
        }
        response = client.post("/users", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == user_data["name"]
        assert data["email"] == user_data["email"]
    
    def test_analytics_endpoint_caching(self):
        """Test analytics endpoint caching"""
        response1 = client.get("/admin/analytics")
        assert response1.status_code == 200
        
        response2 = client.get("/admin/analytics")
        assert response2.status_code == 200
        
        # Should return same cached data
        assert response1.json() == response2.json()
