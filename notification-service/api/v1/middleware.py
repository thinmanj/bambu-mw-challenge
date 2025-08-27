"""
Simple rate limiting headers middleware for the notification service.
Adds rate limiting headers to HTTP responses without authentication dependencies.
"""

import time
import logging
from typing import Dict, Any, Tuple
from collections import defaultdict, deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from fastapi import Request

logger = logging.getLogger(__name__)


class MemoryRateLimiter:
    """Simple in-memory rate limiter using sliding window"""
    
    def __init__(self):
        self.requests = defaultdict(deque)
    
    def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> Tuple[bool, int, int]:
        """
        Check rate limit and return (allowed, remaining, reset_time)
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Clean old requests outside the window
        request_times = self.requests[key]
        while request_times and request_times[0] <= window_start:
            request_times.popleft()
        
        current_requests = len(request_times)
        
        if current_requests >= limit:
            # Rate limit exceeded
            oldest_request = request_times[0] if request_times else now
            reset_time = int(oldest_request + window_seconds)
            return False, 0, reset_time
        
        # Add current request
        request_times.append(now)
        remaining = limit - current_requests - 1
        reset_time = int(now + window_seconds)
        
        return True, remaining, reset_time


class RateLimitHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds rate limiting headers to HTTP responses.
    
    Configuration:
    - RATE_LIMIT_ENABLED: Enable/disable rate limiting (default: True)
    - Default limits: 100/minute, 1000/hour
    - Per-endpoint limits can be configured
    """
    
    def __init__(self, app, **kwargs):
        super().__init__(app)
        
        # Configuration
        self.enabled = kwargs.get('enabled', True)
        self.per_minute_limit = kwargs.get('per_minute', 100)
        self.per_hour_limit = kwargs.get('per_hour', 1000)
        
        # Endpoint-specific limits
        self.endpoint_limits = kwargs.get('endpoint_limits', {
            "/api/v1/notifications/send": {"per_minute": 50},
            "/api/v1/templates": {"per_minute": 30},
        })
        
        # Rate limiter
        self.limiter = MemoryRateLimiter()
        
        logger.info(f"⚡ Rate limit headers middleware initialized - enabled: {self.enabled}")
        if self.enabled:
            logger.info(f"📊 Default limits: {self.per_minute_limit}/min, {self.per_hour_limit}/hour")

    async def dispatch(self, request: Request, call_next):
        """Add rate limiting headers to responses"""
        
        # Skip for health and docs endpoints
        if self._should_skip_rate_limit(request.url.path):
            return await call_next(request)
        
        response = await call_next(request)
        
        if self.enabled:
            await self._add_rate_limit_headers(request, response)
        
        return response
    
    async def _add_rate_limit_headers(self, request: Request, response: Response):
        """Add rate limit headers to the response"""
        try:
            client_ip = self._get_client_ip(request)
            path = request.url.path
            
            # Get rate limits for this endpoint
            minute_limit = self._get_endpoint_limit(path, "per_minute", self.per_minute_limit)
            hour_limit = self._get_endpoint_limit(path, "per_hour", self.per_hour_limit)
            
            # Check minute limit
            minute_key = f"ip:{client_ip}:minute"
            minute_allowed, minute_remaining, minute_reset = self.limiter.check_rate_limit(
                minute_key, minute_limit, 60
            )
            
            # Check hour limit
            hour_key = f"ip:{client_ip}:hour"
            hour_allowed, hour_remaining, hour_reset = self.limiter.check_rate_limit(
                hour_key, hour_limit, 3600
            )
            
            # Use the most restrictive limit for headers
            if minute_remaining < hour_remaining:
                remaining = minute_remaining
                reset_time = minute_reset
                limit = minute_limit
                window = "60"
            else:
                remaining = hour_remaining
                reset_time = hour_reset
                limit = hour_limit
                window = "3600"
            
            # Add standard rate limit headers
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
            response.headers["X-RateLimit-Reset"] = str(reset_time)
            response.headers["X-RateLimit-Window"] = window
            
            # Add custom headers for both minute and hour limits
            response.headers["X-RateLimit-Limit-Minute"] = str(minute_limit)
            response.headers["X-RateLimit-Remaining-Minute"] = str(max(0, minute_remaining))
            response.headers["X-RateLimit-Limit-Hour"] = str(hour_limit)
            response.headers["X-RateLimit-Remaining-Hour"] = str(max(0, hour_remaining))
            
            # Log rate limit info for monitoring
            if minute_remaining < 10 or hour_remaining < 50:
                logger.warning(
                    f"⚠️ High rate limit usage - IP: {client_ip}, "
                    f"Path: {path}, Minute: {minute_remaining}/{minute_limit}, "
                    f"Hour: {hour_remaining}/{hour_limit}"
                )
            
        except Exception as e:
            logger.error(f"💥 Error adding rate limit headers: {e}")
    
    def _get_endpoint_limit(self, path: str, limit_type: str, default: int) -> int:
        """Get rate limit for specific endpoint"""
        for pattern, config in self.endpoint_limits.items():
            if self._path_matches_pattern(path, pattern):
                return config.get(limit_type, default)
        return default
    
    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches pattern with wildcards"""
        if "*" not in pattern:
            return path.startswith(pattern)
        
        import re
        regex_pattern = pattern.replace("*", r"[^/]*")
        return bool(re.match(f"^{regex_pattern}", path))
    
    def _should_skip_rate_limit(self, path: str) -> bool:
        """Check if rate limiting should be skipped for this path"""
        skip_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]
        
        # Exact match for root path
        if path == "/":
            return True
            
        # Check other skip paths
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers (when behind proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"

