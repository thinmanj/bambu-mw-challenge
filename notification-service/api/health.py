"""
Health check endpoints for Kubernetes probes and monitoring.
"""
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from database.connection import get_redis_client, get_engine
import redis
import sqlalchemy as sa
from sqlalchemy import text

health_router = APIRouter(prefix="/health", tags=["health"])

# Application state tracking
_startup_complete = False
_startup_time = None

def mark_startup_complete():
    """Mark the application startup as complete"""
    global _startup_complete, _startup_time
    _startup_complete = True
    _startup_time = datetime.utcnow()

async def check_database_connection() -> bool:
    """Check if database connection is healthy"""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Simple query to test connection
            result = conn.execute(text("SELECT 1"))
            return result.fetchone() is not None
    except Exception:
        return False

async def check_redis_connection() -> bool:
    """Check if Redis connection is healthy"""
    try:
        redis_client = await get_redis_client()
        if redis_client:
            # Test Redis connection with a simple ping
            await redis_client.ping()
            return True
        return False
    except Exception:
        return False

@health_router.get("/live")
async def liveness_check():
    """
    Liveness probe - indicates if the service is running.
    
    This endpoint should return 200 if the service process is alive.
    Kubernetes will restart the pod if this fails.
    """
    return {
        "status": "alive",
        "service": "notification-service",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": (datetime.utcnow() - _startup_time).total_seconds() if _startup_time else 0
    }

@health_router.get("/ready")
async def readiness_check():
    """
    Readiness probe - indicates if the service is ready to accept requests.
    
    This endpoint performs dependency checks and returns 200 only if all
    required services (database, Redis) are available.
    Kubernetes will not route traffic to the pod if this fails.
    """
    checks = {}
    healthy = True
    
    # Check database connectivity
    try:
        db_healthy = await check_database_connection()
        checks["database"] = "healthy" if db_healthy else "unhealthy"
        if not db_healthy:
            healthy = False
    except Exception as e:
        checks["database"] = "unhealthy"
        checks["database_error"] = str(e)
        healthy = False
    
    # Check Redis connectivity
    try:
        redis_healthy = await check_redis_connection()
        checks["redis"] = "healthy" if redis_healthy else "unhealthy"
        if not redis_healthy:
            healthy = False
    except Exception as e:
        checks["redis"] = "unhealthy"
        checks["redis_error"] = str(e)
        healthy = False
    
    response = {
        "status": "ready" if healthy else "not_ready",
        "service": "notification-service",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }
    
    if not healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response
        )
    
    return response

@health_router.get("/startup")
async def startup_check():
    """
    Startup probe - indicates if the service has completed initialization.
    
    This endpoint returns 200 only after the application has completed
    all initialization tasks (database connections, cache warming, etc.).
    Kubernetes will not perform liveness/readiness checks until this succeeds.
    """
    if not _startup_complete:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "starting",
                "service": "notification-service",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Application is still initializing"
            }
        )
    
    return {
        "status": "started",
        "service": "notification-service",
        "timestamp": datetime.utcnow().isoformat(),
        "startup_time": _startup_time.isoformat() if _startup_time else None,
        "initialization_duration_seconds": (datetime.utcnow() - _startup_time).total_seconds() if _startup_time else 0
    }

# Legacy health endpoint for backward compatibility
@health_router.get("")
async def health_check():
    """
    Legacy health check endpoint for backward compatibility.
    
    This provides a simple health check that combines basic liveness
    and readiness information.
    """
    checks = {}
    healthy = True
    
    # Check database connectivity
    db_healthy = await check_database_connection()
    checks["database"] = "connected" if db_healthy else "disconnected"
    if not db_healthy:
        healthy = False
    
    # Check Redis connectivity  
    redis_healthy = await check_redis_connection()
    checks["cache"] = "connected" if redis_healthy else "disconnected"
    if not redis_healthy:
        healthy = False
    
    response = {
        "status": "healthy" if healthy else "unhealthy",
        "service": "notification-service",
        "timestamp": datetime.utcnow().isoformat(),
        **checks
    }
    
    if not healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response
        )
    
    return response
