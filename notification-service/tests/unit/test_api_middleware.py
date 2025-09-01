"""
Comprehensive tests for API middleware.

This module tests the rate limiting middleware including the memory rate limiter
and HTTP middleware functionality.
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from collections import deque

from fastapi import Request
from starlette.responses import Response
from starlette.applications import Starlette

from api.v1.middleware import MemoryRateLimiter, RateLimitHeadersMiddleware


@pytest.mark.unit
class TestMemoryRateLimiter:
    """Test the MemoryRateLimiter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.limiter = MemoryRateLimiter()

    def test_initialization(self):
        """Test MemoryRateLimiter initialization."""
        assert isinstance(self.limiter.requests, dict)
        assert len(self.limiter.requests) == 0

    def test_check_rate_limit_under_limit(self):
        """Test rate limit check when under the limit."""
        key = "test_key"
        limit = 5
        window_seconds = 60
        
        allowed, remaining, reset_time = self.limiter.check_rate_limit(key, limit, window_seconds)
        
        assert allowed is True
        assert remaining == 4  # limit - current_requests - 1
        assert isinstance(reset_time, int)
        assert reset_time > time.time()

    def test_check_rate_limit_multiple_requests(self):
        """Test multiple requests within limit."""
        key = "test_key"
        limit = 3
        window_seconds = 60
        
        # First request
        allowed1, remaining1, reset_time1 = self.limiter.check_rate_limit(key, limit, window_seconds)
        assert allowed1 is True
        assert remaining1 == 2
        
        # Second request
        allowed2, remaining2, reset_time2 = self.limiter.check_rate_limit(key, limit, window_seconds)
        assert allowed2 is True
        assert remaining2 == 1
        
        # Third request
        allowed3, remaining3, reset_time3 = self.limiter.check_rate_limit(key, limit, window_seconds)
        assert allowed3 is True
        assert remaining3 == 0

    def test_check_rate_limit_exceed_limit(self):
        """Test rate limit exceeded scenario."""
        key = "test_key"
        limit = 2
        window_seconds = 60
        
        # Use up the limit
        self.limiter.check_rate_limit(key, limit, window_seconds)
        self.limiter.check_rate_limit(key, limit, window_seconds)
        
        # Next request should be blocked
        allowed, remaining, reset_time = self.limiter.check_rate_limit(key, limit, window_seconds)
        
        assert allowed is False
        assert remaining == 0
        assert isinstance(reset_time, int)

    def test_check_rate_limit_window_expiry(self):
        """Test that requests expire after the window."""
        key = "test_key"
        limit = 2
        window_seconds = 1  # Very short window
        
        # Make requests to reach limit
        allowed1, remaining1, _ = self.limiter.check_rate_limit(key, limit, window_seconds)
        allowed2, remaining2, _ = self.limiter.check_rate_limit(key, limit, window_seconds)
        
        assert allowed1 is True
        assert allowed2 is True
        assert remaining2 == 0
        
        # Should be blocked immediately
        allowed3, remaining3, _ = self.limiter.check_rate_limit(key, limit, window_seconds)
        assert allowed3 is False
        assert remaining3 == 0
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should be allowed again
        allowed4, remaining4, _ = self.limiter.check_rate_limit(key, limit, window_seconds)
        assert allowed4 is True
        assert remaining4 == 1

    def test_check_rate_limit_different_keys(self):
        """Test that different keys have separate limits."""
        limit = 2
        window_seconds = 60
        
        # Use up limit for key1
        self.limiter.check_rate_limit("key1", limit, window_seconds)
        self.limiter.check_rate_limit("key1", limit, window_seconds)
        
        # key1 should be blocked
        allowed1, remaining1, _ = self.limiter.check_rate_limit("key1", limit, window_seconds)
        assert allowed1 is False
        assert remaining1 == 0
        
        # key2 should still be allowed
        allowed2, remaining2, _ = self.limiter.check_rate_limit("key2", limit, window_seconds)
        assert allowed2 is True
        assert remaining2 == 1

    def test_check_rate_limit_sliding_window(self):
        """Test sliding window behavior."""
        key = "test_key"
        limit = 3
        window_seconds = 2
        
        # Make requests at specific times
        with patch('time.time') as mock_time:
            # Time 0: First request
            mock_time.return_value = 0
            allowed1, remaining1, _ = self.limiter.check_rate_limit(key, limit, window_seconds)
            assert allowed1 is True
            assert remaining1 == 2
            
            # Time 1: Second request
            mock_time.return_value = 1
            allowed2, remaining2, _ = self.limiter.check_rate_limit(key, limit, window_seconds)
            assert allowed2 is True
            assert remaining2 == 1
            
            # Time 2.5: Third request (first request should still be in window)
            mock_time.return_value = 2.5
            allowed3, remaining3, _ = self.limiter.check_rate_limit(key, limit, window_seconds)
            assert allowed3 is True
            assert remaining3 == 1  # First request (at time 0) expired, so remaining is 1
            
            # Time 3: Fourth request (first and second request expired, only third in window)
            mock_time.return_value = 3
            allowed4, remaining4, _ = self.limiter.check_rate_limit(key, limit, window_seconds)
            assert allowed4 is True
            assert remaining4 == 1  # Only third request (at time 2.5) is still in window, so remaining is 1

    def test_check_rate_limit_edge_cases(self):
        """Test edge cases for rate limiting."""
        key = "test_key"
        limit = 0
        window_seconds = 60
        
        # Zero limit should always block
        allowed, remaining, reset_time = self.limiter.check_rate_limit(key, limit, window_seconds)
        assert allowed is False
        assert remaining == 0

    def test_request_times_cleanup(self):
        """Test that old request times are properly cleaned up."""
        key = "test_key"
        limit = 5
        window_seconds = 1
        
        with patch('time.time') as mock_time:
            # Add some old requests
            mock_time.return_value = 0
            self.limiter.check_rate_limit(key, limit, window_seconds)
            self.limiter.check_rate_limit(key, limit, window_seconds)
            
            # Verify requests are recorded
            assert len(self.limiter.requests[key]) == 2
            
            # Move time forward beyond window
            mock_time.return_value = 2
            
            # Make another request - should clean up old ones
            self.limiter.check_rate_limit(key, limit, window_seconds)
            
            # Should have cleaned up old requests and added new one
            request_times = list(self.limiter.requests[key])
            assert len(request_times) == 1
            assert request_times[0] == 2


@pytest.mark.unit
class TestRateLimitHeadersMiddleware:
    """Test the RateLimitHeadersMiddleware class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = Starlette()

    def test_initialization_default_config(self):
        """Test middleware initialization with default configuration."""
        middleware = RateLimitHeadersMiddleware(self.app)
        
        assert middleware.enabled is True
        assert middleware.per_minute_limit == 100
        assert middleware.per_hour_limit == 1000
        assert isinstance(middleware.endpoint_limits, dict)
        assert isinstance(middleware.limiter, MemoryRateLimiter)

    def test_initialization_custom_config(self):
        """Test middleware initialization with custom configuration."""
        custom_config = {
            'enabled': False,
            'per_minute': 50,
            'per_hour': 500,
            'endpoint_limits': {'/custom': {'per_minute': 10}}
        }
        
        middleware = RateLimitHeadersMiddleware(self.app, **custom_config)
        
        assert middleware.enabled is False
        assert middleware.per_minute_limit == 50
        assert middleware.per_hour_limit == 500
        assert middleware.endpoint_limits == {'/custom': {'per_minute': 10}}

    def test_should_skip_rate_limit(self):
        """Test which paths should skip rate limiting."""
        middleware = RateLimitHeadersMiddleware(self.app)
        
        # Should skip
        assert middleware._should_skip_rate_limit("/") is True
        assert middleware._should_skip_rate_limit("/health") is True
        assert middleware._should_skip_rate_limit("/health/live") is True
        assert middleware._should_skip_rate_limit("/docs") is True
        assert middleware._should_skip_rate_limit("/redoc") is True
        assert middleware._should_skip_rate_limit("/openapi.json") is True
        assert middleware._should_skip_rate_limit("/favicon.ico") is True
        
        # Should not skip
        assert middleware._should_skip_rate_limit("/api/v1/notifications") is False
        assert middleware._should_skip_rate_limit("/api/v1/templates") is False
        assert middleware._should_skip_rate_limit("/custom/path") is False

    def test_get_client_ip_forwarded_for(self):
        """Test getting client IP from X-Forwarded-For header."""
        middleware = RateLimitHeadersMiddleware(self.app)
        
        # Mock request with X-Forwarded-For header
        mock_request = Mock()
        mock_request.headers = {"x-forwarded-for": "192.168.1.1, 10.0.0.1"}
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.1"

    def test_get_client_ip_real_ip(self):
        """Test getting client IP from X-Real-IP header."""
        middleware = RateLimitHeadersMiddleware(self.app)
        
        # Mock request with X-Real-IP header
        mock_request = Mock()
        mock_request.headers = {"x-real-ip": "192.168.1.2"}
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.2"

    def test_get_client_ip_client_host(self):
        """Test getting client IP from request.client.host."""
        middleware = RateLimitHeadersMiddleware(self.app)
        
        # Mock request with client.host
        mock_request = Mock()
        mock_request.headers = {}
        mock_request.client.host = "192.168.1.3"
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.3"

    def test_get_client_ip_fallback(self):
        """Test fallback when no IP is available."""
        middleware = RateLimitHeadersMiddleware(self.app)
        
        # Mock request with no IP information
        mock_request = Mock()
        mock_request.headers = {}
        mock_request.client = None
        
        ip = middleware._get_client_ip(mock_request)
        assert ip == "unknown"

    def test_get_client_ip_priority_order(self):
        """Test that IP headers are checked in correct priority order."""
        middleware = RateLimitHeadersMiddleware(self.app)
        
        # Mock request with multiple IP sources
        mock_request = Mock()
        mock_request.headers = {
            "x-forwarded-for": "192.168.1.1",
            "x-real-ip": "192.168.1.2"
        }
        mock_request.client.host = "192.168.1.3"
        
        # Should prioritize X-Forwarded-For
        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.1"

    def test_path_matches_pattern_exact(self):
        """Test exact path pattern matching."""
        middleware = RateLimitHeadersMiddleware(self.app)
        
        assert middleware._path_matches_pattern("/api/v1/templates", "/api/v1/templates") is True
        assert middleware._path_matches_pattern("/api/v1/templates/123", "/api/v1/templates") is True
        assert middleware._path_matches_pattern("/api/v1/notifications", "/api/v1/templates") is False

    def test_path_matches_pattern_wildcard(self):
        """Test wildcard path pattern matching."""
        middleware = RateLimitHeadersMiddleware(self.app)
        
        assert middleware._path_matches_pattern("/api/v1/users/123", "/api/v1/users/*") is True
        assert middleware._path_matches_pattern("/api/v1/users/abc", "/api/v1/users/*") is True
        assert middleware._path_matches_pattern("/api/v1/users/123/posts", "/api/v1/users/*") is True  # Pattern allows subdirectories

    def test_get_endpoint_limit_default(self):
        """Test getting default endpoint limit."""
        middleware = RateLimitHeadersMiddleware(self.app)
        
        limit = middleware._get_endpoint_limit("/unknown/path", "per_minute", 100)
        assert limit == 100

    def test_get_endpoint_limit_custom(self):
        """Test getting custom endpoint limit."""
        endpoint_limits = {
            "/api/v1/notifications/send": {"per_minute": 50},
            "/api/v1/templates": {"per_minute": 30, "per_hour": 300}
        }
        middleware = RateLimitHeadersMiddleware(self.app, endpoint_limits=endpoint_limits)
        
        # Test configured endpoints
        assert middleware._get_endpoint_limit("/api/v1/notifications/send", "per_minute", 100) == 50
        assert middleware._get_endpoint_limit("/api/v1/templates", "per_minute", 100) == 30
        assert middleware._get_endpoint_limit("/api/v1/templates", "per_hour", 1000) == 300
        
        # Test fallback to default for missing limit type
        assert middleware._get_endpoint_limit("/api/v1/notifications/send", "per_hour", 1000) == 1000

    @pytest.mark.asyncio
    async def test_dispatch_skip_paths(self):
        """Test that dispatch skips rate limiting for certain paths."""
        middleware = RateLimitHeadersMiddleware(self.app)
        
        # Mock request for health endpoint
        mock_request = Mock()
        mock_request.url.path = "/health"
        
        # Mock call_next
        mock_response = Mock()
        call_next = AsyncMock(return_value=mock_response)
        
        # Should skip rate limiting and return response directly
        result = await middleware.dispatch(mock_request, call_next)
        
        assert result == mock_response
        call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_dispatch_disabled(self):
        """Test dispatch when rate limiting is disabled."""
        middleware = RateLimitHeadersMiddleware(self.app, enabled=False)
        
        # Mock request
        mock_request = Mock()
        mock_request.url.path = "/api/v1/templates"
        
        # Mock response
        mock_response = Mock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)
        
        # Should not add rate limit headers
        result = await middleware.dispatch(mock_request, call_next)
        
        assert result == mock_response
        assert len(mock_response.headers) == 0

    @pytest.mark.asyncio
    async def test_dispatch_enabled(self):
        """Test dispatch when rate limiting is enabled."""
        middleware = RateLimitHeadersMiddleware(self.app, enabled=True)
        
        # Mock request
        mock_request = Mock()
        mock_request.url.path = "/api/v1/templates"
        mock_request.headers = {}
        mock_request.client.host = "192.168.1.1"
        
        # Mock response
        mock_response = Mock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)
        
        # Should add rate limit headers
        with patch.object(middleware, '_add_rate_limit_headers', new_callable=AsyncMock) as mock_add_headers:
            result = await middleware.dispatch(mock_request, call_next)
            
            assert result == mock_response
            mock_add_headers.assert_called_once_with(mock_request, mock_response)

    @pytest.mark.asyncio
    async def test_add_rate_limit_headers(self):
        """Test adding rate limit headers to response."""
        middleware = RateLimitHeadersMiddleware(self.app, per_minute=10, per_hour=100)
        
        # Mock request
        mock_request = Mock()
        mock_request.url.path = "/api/v1/templates"
        mock_request.headers = {}
        mock_request.client.host = "192.168.1.1"
        
        # Mock response
        mock_response = Mock()
        mock_response.headers = {}
        
        # Mock rate limiter responses
        with patch.object(middleware.limiter, 'check_rate_limit') as mock_check:
            # First call (minute limit): allowed=True, remaining=5, reset_time=1640995200
            # Second call (hour limit): allowed=True, remaining=50, reset_time=1640998800
            mock_check.side_effect = [
                (True, 5, 1640995200),  # minute
                (True, 50, 1640998800)  # hour
            ]
            
            await middleware._add_rate_limit_headers(mock_request, mock_response)
            
            # Check that headers were added - /api/v1/templates has endpoint-specific limit of 30/min
            assert mock_response.headers["X-RateLimit-Limit"] == "30"  # Endpoint-specific limit for /api/v1/templates
            assert mock_response.headers["X-RateLimit-Remaining"] == "5"
            assert mock_response.headers["X-RateLimit-Reset"] == "1640995200"
            assert mock_response.headers["X-RateLimit-Window"] == "60"
            
            # Check detailed headers
            assert mock_response.headers["X-RateLimit-Limit-Minute"] == "30"
            assert mock_response.headers["X-RateLimit-Remaining-Minute"] == "5"
            assert mock_response.headers["X-RateLimit-Limit-Hour"] == "100"
            assert mock_response.headers["X-RateLimit-Remaining-Hour"] == "50"

    @pytest.mark.asyncio
    async def test_add_rate_limit_headers_hour_more_restrictive(self):
        """Test headers when hour limit is more restrictive."""
        middleware = RateLimitHeadersMiddleware(self.app, per_minute=100, per_hour=10)
        
        # Mock request
        mock_request = Mock()
        mock_request.url.path = "/api/v1/templates"
        mock_request.headers = {}
        mock_request.client.host = "192.168.1.1"
        
        # Mock response
        mock_response = Mock()
        mock_response.headers = {}
        
        # Mock rate limiter responses
        with patch.object(middleware.limiter, 'check_rate_limit') as mock_check:
            # Minute limit has more remaining, hour limit is more restrictive
            mock_check.side_effect = [
                (True, 50, 1640995200),  # minute
                (True, 2, 1640998800)    # hour (more restrictive)
            ]
            
            await middleware._add_rate_limit_headers(mock_request, mock_response)
            
            # Should use hour limit for main headers
            assert mock_response.headers["X-RateLimit-Limit"] == "10"
            assert mock_response.headers["X-RateLimit-Remaining"] == "2"
            assert mock_response.headers["X-RateLimit-Reset"] == "1640998800"
            assert mock_response.headers["X-RateLimit-Window"] == "3600"

    @pytest.mark.asyncio
    async def test_add_rate_limit_headers_custom_endpoint_limits(self):
        """Test rate limit headers with custom endpoint limits."""
        endpoint_limits = {
            "/api/v1/notifications/send": {"per_minute": 20, "per_hour": 200}
        }
        middleware = RateLimitHeadersMiddleware(
            self.app, 
            per_minute=100, 
            per_hour=1000,
            endpoint_limits=endpoint_limits
        )
        
        # Mock request to custom endpoint
        mock_request = Mock()
        mock_request.url.path = "/api/v1/notifications/send"
        mock_request.headers = {}
        mock_request.client.host = "192.168.1.1"
        
        # Mock response
        mock_response = Mock()
        mock_response.headers = {}
        
        with patch.object(middleware.limiter, 'check_rate_limit') as mock_check:
            mock_check.side_effect = [
                (True, 10, 1640995200),  # minute
                (True, 100, 1640998800)  # hour
            ]
            
            await middleware._add_rate_limit_headers(mock_request, mock_response)
            
            # Should use custom limits
            assert mock_response.headers["X-RateLimit-Limit-Minute"] == "20"
            assert mock_response.headers["X-RateLimit-Limit-Hour"] == "200"
            
            # Verify limiter was called with custom limits
            assert mock_check.call_count == 2
            minute_call = mock_check.call_args_list[0]
            hour_call = mock_check.call_args_list[1]
            assert minute_call[0][1] == 20  # minute limit
            assert hour_call[0][1] == 200   # hour limit

    @pytest.mark.asyncio
    async def test_add_rate_limit_headers_warning_log(self):
        """Test warning log when rate limits are running low."""
        middleware = RateLimitHeadersMiddleware(self.app)
        
        # Mock request
        mock_request = Mock()
        mock_request.url.path = "/api/v1/templates"
        mock_request.headers = {}
        mock_request.client.host = "192.168.1.1"
        
        # Mock response
        mock_response = Mock()
        mock_response.headers = {}
        
        with patch.object(middleware.limiter, 'check_rate_limit') as mock_check:
            with patch('api.v1.middleware.logger') as mock_logger:
                # Low remaining requests should trigger warning
                mock_check.side_effect = [
                    (True, 5, 1640995200),   # minute - below 10 threshold
                    (True, 30, 1640998800)   # hour - below 50 threshold
                ]
                
                await middleware._add_rate_limit_headers(mock_request, mock_response)
                
                # Should have logged warning
                mock_logger.warning.assert_called_once()
                warning_call = mock_logger.warning.call_args[0][0]
                assert "High rate limit usage" in warning_call
                assert "192.168.1.1" in warning_call

    @pytest.mark.asyncio
    async def test_add_rate_limit_headers_exception_handling(self):
        """Test exception handling in _add_rate_limit_headers."""
        middleware = RateLimitHeadersMiddleware(self.app)
        
        # Mock request
        mock_request = Mock()
        mock_request.url.path = "/api/v1/templates"
        
        # Mock response
        mock_response = Mock()
        mock_response.headers = {}
        
        with patch.object(middleware, '_get_client_ip', side_effect=Exception("Test error")):
            with patch('api.v1.middleware.logger') as mock_logger:
                # Should not raise exception
                await middleware._add_rate_limit_headers(mock_request, mock_response)
                
                # Should log error
                mock_logger.error.assert_called_once()
                error_call = mock_logger.error.call_args[0][0]
                assert "Error adding rate limit headers" in error_call

    @pytest.mark.asyncio
    async def test_negative_remaining_headers(self):
        """Test that remaining headers never go negative."""
        middleware = RateLimitHeadersMiddleware(self.app)
        
        # Mock request
        mock_request = Mock()
        mock_request.url.path = "/api/v1/templates"
        mock_request.headers = {}
        mock_request.client.host = "192.168.1.1"
        
        # Mock response
        mock_response = Mock()
        mock_response.headers = {}
        
        with patch.object(middleware.limiter, 'check_rate_limit') as mock_check:
            # Simulate negative remaining (edge case)
            mock_check.side_effect = [
                (True, -5, 1640995200),  # minute
                (True, -10, 1640998800)  # hour
            ]
            
            await middleware._add_rate_limit_headers(mock_request, mock_response)
            
            # Should not have negative remaining
            assert mock_response.headers["X-RateLimit-Remaining"] == "0"
            assert mock_response.headers["X-RateLimit-Remaining-Minute"] == "0"
            assert mock_response.headers["X-RateLimit-Remaining-Hour"] == "0"

    def test_rate_limiter_keys_format(self):
        """Test that rate limiter keys are formatted correctly."""
        middleware = RateLimitHeadersMiddleware(self.app)
        
        # Mock request
        mock_request = Mock()
        mock_request.url.path = "/api/v1/templates"
        mock_request.headers = {}
        mock_request.client.host = "192.168.1.1"
        
        # Mock response
        mock_response = Mock()
        mock_response.headers = {}
        
        with patch.object(middleware.limiter, 'check_rate_limit') as mock_check:
            mock_check.return_value = (True, 10, 1640995200)
            
            # Run the method
            import asyncio
            asyncio.run(middleware._add_rate_limit_headers(mock_request, mock_response))
            
            # Verify the keys passed to rate limiter
            assert mock_check.call_count == 2
            
            minute_call = mock_check.call_args_list[0]
            hour_call = mock_check.call_args_list[1]
            
            assert minute_call[0][0] == "ip:192.168.1.1:minute"
            assert hour_call[0][0] == "ip:192.168.1.1:hour"
            
            # Verify window times
            assert minute_call[0][2] == 60    # minute window
            assert hour_call[0][2] == 3600    # hour window


@pytest.mark.unit
class TestMiddlewareIntegration:
    """Test integration scenarios for the middleware."""

    @pytest.mark.asyncio
    async def test_full_request_cycle(self):
        """Test a complete request cycle through the middleware."""
        # Create middleware with custom configuration
        app = Starlette()
        middleware = RateLimitHeadersMiddleware(
            app,
            enabled=True,
            per_minute=5,
            per_hour=50
        )
        
        # Mock a complete request
        mock_request = Mock()
        mock_request.url.path = "/api/v1/notifications"
        mock_request.headers = {"x-forwarded-for": "203.0.113.1"}
        mock_request.client = None
        
        # Mock response from downstream
        mock_response = Mock()
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        # Execute the middleware
        result = await middleware.dispatch(mock_request, mock_call_next)
        
        # Verify response is returned
        assert result == mock_response
        
        # Verify headers were added
        assert "X-RateLimit-Limit" in mock_response.headers
        assert "X-RateLimit-Remaining" in mock_response.headers
        assert "X-RateLimit-Reset" in mock_response.headers
        assert "X-RateLimit-Window" in mock_response.headers

    @pytest.mark.asyncio
    async def test_concurrent_requests_same_ip(self):
        """Test concurrent requests from the same IP."""
        app = Starlette()
        middleware = RateLimitHeadersMiddleware(app, per_minute=3, per_hour=10)
        
        async def make_request(path="/api/v1/test"):
            mock_request = Mock()
            mock_request.url.path = path
            mock_request.headers = {}
            mock_request.client.host = "192.168.1.1"
            
            mock_response = Mock()
            mock_response.headers = {}
            
            async def mock_call_next(request):
                return mock_response
            
            await middleware.dispatch(mock_request, mock_call_next)
            return mock_response.headers.get("X-RateLimit-Remaining-Minute", "0")
        
        # Make several requests
        remaining_counts = []
        for i in range(4):
            remaining = await make_request()
            remaining_counts.append(int(remaining))
        
        # Should see decreasing remaining counts
        assert remaining_counts[0] > remaining_counts[1]
        assert remaining_counts[1] > remaining_counts[2]
        assert remaining_counts[2] >= remaining_counts[3]  # Might be blocked

    @pytest.mark.asyncio
    async def test_different_endpoints_different_limits(self):
        """Test that different endpoints can have different limits."""
        endpoint_limits = {
            "/api/v1/high-frequency": {"per_minute": 100},
            "/api/v1/low-frequency": {"per_minute": 5}
        }
        
        app = Starlette()
        middleware = RateLimitHeadersMiddleware(
            app,
            per_minute=50,
            endpoint_limits=endpoint_limits
        )
        
        # Test high-frequency endpoint
        async def test_endpoint(path, expected_limit):
            mock_request = Mock()
            mock_request.url.path = path
            mock_request.headers = {}
            mock_request.client.host = f"192.168.1.{hash(path) % 100}"  # Different IP per path
            
            mock_response = Mock()
            mock_response.headers = {}
            
            async def mock_call_next(request):
                return mock_response
            
            await middleware.dispatch(mock_request, mock_call_next)
            return mock_response.headers.get("X-RateLimit-Limit-Minute")
        
        high_freq_limit = await test_endpoint("/api/v1/high-frequency", "100")
        low_freq_limit = await test_endpoint("/api/v1/low-frequency", "5")
        default_limit = await test_endpoint("/api/v1/default", "50")
        
        assert high_freq_limit == "100"
        assert low_freq_limit == "5"
        assert default_limit == "50"
