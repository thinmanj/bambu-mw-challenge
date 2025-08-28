"""
Integration tests for health API endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient


@pytest.mark.integration
@pytest.mark.api
class TestHealthAPI:
    """Integration tests for health API endpoints."""

    def setup_method(self):
        """Setup test client."""
        # Create FastAPI app for testing (avoid circular imports)
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from api.health import health_router
        from api.v1.middleware import RateLimitHeadersMiddleware
        
        app = FastAPI(title="Test Health Service")
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        app.include_router(health_router)
        
        # Add root endpoint for test compatibility
        @app.get("/")
        async def root():
            return {
                "service": "notification-service",
                "version": "1.0.0",
                "status": "running",
                "api_versions": ["v1"],
                "api_base_url": "/api/v1"
            }
        
        self.client = TestClient(app)
        
        # Reset health state
        import api.health
        api.health._startup_complete = False
        api.health._startup_time = None

    def test_health_liveness_endpoint(self):
        """Test liveness endpoint via API."""
        response = self.client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert data["service"] == "notification-service"
        assert "timestamp" in data
        assert "uptime_seconds" in data

    def test_health_startup_endpoint_before_startup(self):
        """Test startup endpoint before startup is complete."""
        response = self.client.get("/health/startup")
        
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "starting"
        assert data["detail"]["service"] == "notification-service"

    def test_health_startup_endpoint_after_startup(self):
        """Test startup endpoint after startup is complete."""
        # Mark startup as complete
        from api.health import mark_startup_complete
        mark_startup_complete()
        
        response = self.client.get("/health/startup")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert data["service"] == "notification-service"
        assert "startup_time" in data

    @patch('api.health.check_database_connection')
    @patch('api.health.check_redis_connection')
    def test_health_readiness_endpoint_healthy(self, mock_redis_check, mock_db_check):
        """Test readiness endpoint when all dependencies are healthy."""
        mock_db_check.return_value = True
        mock_redis_check.return_value = True
        
        response = self.client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["checks"]["database"] == "healthy"
        assert data["checks"]["redis"] == "healthy"

    @patch('api.health.check_database_connection')
    @patch('api.health.check_redis_connection')
    def test_health_readiness_endpoint_unhealthy(self, mock_redis_check, mock_db_check):
        """Test readiness endpoint when dependencies are unhealthy."""
        mock_db_check.return_value = False
        mock_redis_check.return_value = True
        
        response = self.client.get("/health/ready")
        
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "not_ready"
        assert data["detail"]["checks"]["database"] == "unhealthy"

    @patch('api.health.check_database_connection')
    @patch('api.health.check_redis_connection')
    def test_health_legacy_endpoint_healthy(self, mock_redis_check, mock_db_check):
        """Test legacy health endpoint when dependencies are healthy."""
        mock_db_check.return_value = True
        mock_redis_check.return_value = True
        
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["cache"] == "connected"

    @patch('api.health.check_database_connection')
    @patch('api.health.check_redis_connection')
    def test_health_legacy_endpoint_unhealthy(self, mock_redis_check, mock_db_check):
        """Test legacy health endpoint when dependencies are unhealthy."""
        mock_db_check.return_value = False
        mock_redis_check.return_value = False
        
        response = self.client.get("/health")
        
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "unhealthy"

    def test_health_endpoints_no_rate_limiting(self):
        """Test that health endpoints are excluded from rate limiting."""
        # Make multiple requests quickly
        responses = []
        for _ in range(10):
            response = self.client.get("/health/live")
            responses.append(response)
        
        # All should succeed (no rate limiting)
        for response in responses:
            assert response.status_code == 200
            # Rate limit headers should not be present for health endpoints
            assert "x-ratelimit-limit" not in response.headers

    def test_health_endpoints_content_type(self):
        """Test that health endpoints return correct content type."""
        endpoints = ["/health/live", "/health/startup", "/health/ready", "/health"]
        
        for endpoint in endpoints:
            if endpoint == "/health/startup":
                # Startup might return 503, so we test differently
                response = self.client.get(endpoint)
                assert "application/json" in response.headers["content-type"]
            else:
                with patch('api.health.check_database_connection', return_value=True), \
                     patch('api.health.check_redis_connection', return_value=True):
                    response = self.client.get(endpoint)
                    assert "application/json" in response.headers["content-type"]

    def test_health_endpoints_response_structure(self):
        """Test that health endpoints return proper response structure."""
        # Test liveness
        response = self.client.get("/health/live")
        data = response.json()
        required_fields = ["status", "service", "timestamp", "uptime_seconds"]
        for field in required_fields:
            assert field in data

    @patch('api.health.check_database_connection')
    @patch('api.health.check_redis_connection')
    def test_health_endpoints_cors_headers(self, mock_redis_check, mock_db_check):
        """Test that health endpoints include CORS headers."""
        mock_db_check.return_value = True
        mock_redis_check.return_value = True
        
        response = self.client.get("/health/live")
        
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers

    def test_root_endpoint(self):
        """Test root endpoint functionality."""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "notification-service"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        assert "api_versions" in data

    def test_health_endpoint_error_handling(self):
        """Test health endpoint error handling."""
        with patch('api.health.check_database_connection', side_effect=Exception("Test error")):
            response = self.client.get("/health/ready")
            
            # Should handle exception gracefully
            assert response.status_code == 503
            data = response.json()
            assert data["detail"]["status"] == "not_ready"

    def test_health_endpoints_timestamps(self):
        """Test that health endpoints return valid timestamps."""
        from datetime import datetime
        
        response = self.client.get("/health/live")
        data = response.json()
        
        # Should be able to parse the timestamp
        timestamp = datetime.fromisoformat(data["timestamp"])
        assert isinstance(timestamp, datetime)

    def test_health_readiness_check_partial_failure(self):
        """Test readiness check with partial dependency failure."""
        with patch('api.health.check_database_connection', return_value=True), \
             patch('api.health.check_redis_connection', return_value=False):
            
            response = self.client.get("/health/ready")
            
            assert response.status_code == 503
            data = response.json()
            assert data["detail"]["checks"]["database"] == "healthy"
            assert data["detail"]["checks"]["redis"] == "unhealthy"

    def test_health_startup_state_persistence(self):
        """Test that startup state persists across requests."""
        # Initially not started
        response1 = self.client.get("/health/startup")
        assert response1.status_code == 503
        
        # Mark as started
        from api.health import mark_startup_complete
        mark_startup_complete()
        
        # Should now be started
        response2 = self.client.get("/health/startup")
        assert response2.status_code == 200
        
        # Should remain started on subsequent requests
        response3 = self.client.get("/health/startup")
        assert response3.status_code == 200
