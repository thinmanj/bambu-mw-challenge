from fastapi import APIRouter
from .routes import notifications_router

# Create v1 API router
api_v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

# Include all v1 routes
api_v1_router.include_router(notifications_router)

# Version info endpoint
@api_v1_router.get("/version")
async def get_version():
    """Get API version information"""
    return {
        "version": "1.0.0",
        "api_version": "v1",
        "endpoints": [
            "/api/v1/notifications/send",
            "/api/v1/notifications/{notification_id}",
        ]
    }
