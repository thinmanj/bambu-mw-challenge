from fastapi import APIRouter
from .routes import notifications_router, templates_router, preferences_router

# Create v1 API router
api_v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

# Include all v1 routes
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(templates_router)
api_v1_router.include_router(preferences_router)

# Version info endpoint
@api_v1_router.get("/version")
async def get_version():
    """Get API version information"""
    return {
        "version": "1.0.0",
        "api_version": "v1",
        "notification_management": [
            "POST /api/v1/notifications/send",
            "GET /api/v1/notifications/{id}",
            "GET /api/v1/notifications/user/{user_id}",
            "PUT /api/v1/notifications/{id}/status",
        ],
        "template_management": [
            "GET /api/v1/templates",
            "POST /api/v1/templates",
            "GET /api/v1/templates/{id}",
            "PUT /api/v1/templates/{id}",
            "DELETE /api/v1/templates/{id}",
        ],
        "user_preferences": [
            "GET /api/v1/preferences/user/{user_id}",
            "PUT /api/v1/preferences/user/{user_id}",
        ]
    }
