import uuid
from datetime import datetime
from typing import Dict, Any
from .models import NotificationRequest, NotificationResponse, NotificationStatus, NotificationStatusResponse
from database.connection import get_redis_client

class NotificationService:
    """Minimal notification service implementation"""
    
    async def send_notification(self, request: NotificationRequest) -> NotificationResponse:
        """Send a notification (minimal implementation)"""
        notification_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        # Store notification status in Redis for quick lookup
        redis_client = await get_redis_client()
        notification_data = {
            "id": notification_id,
            "status": NotificationStatus.PENDING.value,
            "recipient": request.recipient,
            "type": request.type.value,
            "message": request.message,
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat()
        }
        
        await redis_client.hset(
            f"notification:{notification_id}",
            mapping=notification_data
        )
        
        # TODO: Implement actual sending logic using adapters
        # For now, just return a pending response
        
        return NotificationResponse(
            id=notification_id,
            status=NotificationStatus.PENDING,
            message=f"Notification queued for {request.recipient}",
            created_at=created_at
        )
    
    async def get_notification_status(self, notification_id: str) -> NotificationStatusResponse:
        """Get notification status"""
        redis_client = await get_redis_client()
        notification_data = await redis_client.hgetall(f"notification:{notification_id}")
        
        if not notification_data:
            raise ValueError(f"Notification {notification_id} not found")
        
        return NotificationStatusResponse(
            id=notification_data["id"],
            status=NotificationStatus(notification_data["status"]),
            created_at=datetime.fromisoformat(notification_data["created_at"]),
            updated_at=datetime.fromisoformat(notification_data["updated_at"]),
            error_message=notification_data.get("error_message")
        )
