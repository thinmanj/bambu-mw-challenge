from fastapi import APIRouter, HTTPException
from core.models import NotificationRequest, NotificationResponse, NotificationStatusResponse
from core.services import NotificationService

# Notifications router
notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])
notification_service = NotificationService()

@notifications_router.post("/send", response_model=NotificationResponse)
async def send_notification(request: NotificationRequest):
    """Send a notification"""
    try:
        return await notification_service.send_notification(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@notifications_router.get("/{notification_id}", response_model=NotificationStatusResponse)
async def get_notification_status(notification_id: str):
    """Get notification status"""
    try:
        return await notification_service.get_notification_status(notification_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))