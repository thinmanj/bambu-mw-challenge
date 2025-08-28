"""
Unit tests for health endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException


@pytest.mark.unit
class TestHealthEndpoints:
    """Test cases for health endpoints."""

    def setup_method(self):
        """Setup test environment."""
        # Reset startup state before each test
        import api.health
        api.health._startup_complete = False
        api.health._startup_time = None

    def test_liveness_check_before_startup(self):
        """Test liveness check before startup is complete."""
        from api.health import liveness_check
        import asyncio
        
        result = asyncio.run(liveness_check())
        
        assert result['status'] == 'alive'
        assert result['service'] == 'notification-service'
        assert 'timestamp' in result
        assert result['uptime_seconds'] == 0  # No startup time set

    def test_liveness_check_after_startup(self):
        """Test liveness check after startup is complete."""
        from api.health import liveness_check, mark_startup_complete
        import asyncio
        
        # Mark startup as complete
        mark_startup_complete()
        
        result = asyncio.run(liveness_check())
        
        assert result['status'] == 'alive'
        assert result['service'] == 'notification-service'
        assert 'timestamp' in result
        assert result['uptime_seconds'] > 0

    def test_startup_check_not_complete(self):
        """Test startup check when startup is not complete."""
        from api.health import startup_check
        import asyncio
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(startup_check())
        
        assert exc_info.value.status_code == 503
        assert exc_info.value.detail['status'] == 'starting'

    def test_startup_check_complete(self):
        """Test startup check when startup is complete."""
        from api.health import startup_check, mark_startup_complete
        import asyncio
        
        # Mark startup as complete
        mark_startup_complete()
        
        result = asyncio.run(startup_check())
        
        assert result['status'] == 'started'
        assert result['service'] == 'notification-service'
        assert 'startup_time' in result
        assert result['initialization_duration_seconds'] >= 0

    @pytest.mark.asyncio
    async def test_readiness_check_healthy(self, mock_health_dependencies):
        """Test readiness check when all dependencies are healthy."""
        from api.health import readiness_check
        
        with patch('api.health.check_database_connection', return_value=True), \
             patch('api.health.check_redis_connection', return_value=True):
            
            result = await readiness_check()
            
            assert result['status'] == 'ready'
            assert result['service'] == 'notification-service'
            assert result['checks']['database'] == 'healthy'
            assert result['checks']['redis'] == 'healthy'

    @pytest.mark.asyncio
    async def test_readiness_check_database_unhealthy(self):
        """Test readiness check when database is unhealthy."""
        from api.health import readiness_check
        
        with patch('api.health.check_database_connection', return_value=False), \
             patch('api.health.check_redis_connection', return_value=True):
            
            with pytest.raises(HTTPException) as exc_info:
                await readiness_check()
            
            assert exc_info.value.status_code == 503
            assert exc_info.value.detail['status'] == 'not_ready'
            assert exc_info.value.detail['checks']['database'] == 'unhealthy'

    @pytest.mark.asyncio
    async def test_readiness_check_redis_unhealthy(self):
        """Test readiness check when Redis is unhealthy."""
        from api.health import readiness_check
        
        with patch('api.health.check_database_connection', return_value=True), \
             patch('api.health.check_redis_connection', return_value=False):
            
            with pytest.raises(HTTPException) as exc_info:
                await readiness_check()
            
            assert exc_info.value.status_code == 503
            assert exc_info.value.detail['status'] == 'not_ready'
            assert exc_info.value.detail['checks']['redis'] == 'unhealthy'

    @pytest.mark.asyncio
    async def test_readiness_check_all_unhealthy(self):
        """Test readiness check when all dependencies are unhealthy."""
        from api.health import readiness_check
        
        with patch('api.health.check_database_connection', return_value=False), \
             patch('api.health.check_redis_connection', return_value=False):
            
            with pytest.raises(HTTPException) as exc_info:
                await readiness_check()
            
            assert exc_info.value.status_code == 503
            assert exc_info.value.detail['checks']['database'] == 'unhealthy'
            assert exc_info.value.detail['checks']['redis'] == 'unhealthy'

    @pytest.mark.asyncio
    async def test_legacy_health_check_healthy(self):
        """Test legacy health check when all dependencies are healthy."""
        from api.health import health_check
        
        with patch('api.health.check_database_connection', return_value=True), \
             patch('api.health.check_redis_connection', return_value=True):
            
            result = await health_check()
            
            assert result['status'] == 'healthy'
            assert result['service'] == 'notification-service'
            assert result['database'] == 'connected'
            assert result['cache'] == 'connected'

    @pytest.mark.asyncio
    async def test_legacy_health_check_unhealthy(self):
        """Test legacy health check when dependencies are unhealthy."""
        from api.health import health_check
        
        with patch('api.health.check_database_connection', return_value=False), \
             patch('api.health.check_redis_connection', return_value=True):
            
            with pytest.raises(HTTPException) as exc_info:
                await health_check()
            
            assert exc_info.value.status_code == 503
            assert exc_info.value.detail['status'] == 'unhealthy'

    @pytest.mark.asyncio
    async def test_check_database_connection_success(self):
        """Test database connection check success."""
        from api.health import check_database_connection
        
        with patch('api.health.get_engine') as mock_get_engine:
            mock_engine = MagicMock()
            mock_connection = MagicMock()
            mock_result = MagicMock()
            
            mock_get_engine.return_value = mock_engine
            mock_engine.connect.return_value.__enter__.return_value = mock_connection
            mock_connection.execute.return_value = mock_result
            mock_result.fetchone.return_value = [1]
            
            result = await check_database_connection()
            
            assert result is True

    @pytest.mark.asyncio
    async def test_check_database_connection_failure(self):
        """Test database connection check failure."""
        from api.health import check_database_connection
        
        with patch('api.health.get_engine') as mock_get_engine:
            mock_get_engine.side_effect = Exception("Database error")
            
            result = await check_database_connection()
            
            assert result is False

    @pytest.mark.asyncio
    async def test_check_redis_connection_success(self):
        """Test Redis connection check success."""
        from api.health import check_redis_connection
        
        with patch('api.health.get_redis_client') as mock_get_redis:
            mock_redis_client = AsyncMock()
            mock_redis_client.ping = AsyncMock(return_value=True)
            mock_get_redis.return_value = mock_redis_client
            
            result = await check_redis_connection()
            
            assert result is True

    @pytest.mark.asyncio
    async def test_check_redis_connection_failure(self):
        """Test Redis connection check failure."""
        from api.health import check_redis_connection
        
        with patch('api.health.get_redis_client') as mock_get_redis:
            mock_get_redis.side_effect = Exception("Redis error")
            
            result = await check_redis_connection()
            
            assert result is False

    @pytest.mark.asyncio
    async def test_check_redis_connection_no_client(self):
        """Test Redis connection check when no client is available."""
        from api.health import check_redis_connection
        
        with patch('api.health.get_redis_client', return_value=None):
            result = await check_redis_connection()
            
            assert result is False

    def test_mark_startup_complete(self):
        """Test marking startup as complete."""
        from api.health import mark_startup_complete, _startup_complete, _startup_time
        
        # Initially not complete
        assert not _startup_complete
        assert _startup_time is None
        
        # Mark as complete
        mark_startup_complete()
        
        # Check state
        from api.health import _startup_complete, _startup_time
        assert _startup_complete
        assert _startup_time is not None

    def test_health_router_endpoints_exist(self):
        """Test that all health endpoints are properly defined."""
        from api.health import health_router
    
        # Check that the router has the expected routes
        route_paths = [route.path for route in health_router.routes]
    
        expected_paths = ['/health/live', '/health/ready', '/health/startup', '/health']
        for path in expected_paths:
            assert path in route_paths

    def test_health_endpoints_response_structure(self):
        """Test that health endpoints have proper response structure."""
        from api.health import liveness_check, mark_startup_complete
        import asyncio
        
        # Test liveness response structure
        mark_startup_complete()
        liveness_result = asyncio.run(liveness_check())
        
        required_fields = ['status', 'service', 'timestamp', 'uptime_seconds']
        for field in required_fields:
            assert field in liveness_result
            
        assert isinstance(liveness_result['status'], str)
        assert isinstance(liveness_result['service'], str)
        assert isinstance(liveness_result['timestamp'], str)
        assert isinstance(liveness_result['uptime_seconds'], (int, float))

    def test_health_endpoints_timestamps_format(self):
        """Test that timestamps are in ISO format."""
        from api.health import liveness_check
        import asyncio
        from datetime import datetime
        
        result = asyncio.run(liveness_check())
        
        # Should be able to parse the timestamp
        timestamp = datetime.fromisoformat(result['timestamp'])
        assert isinstance(timestamp, datetime)
