from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime

class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"

class NotificationRequest(BaseModel):
    recipient: str
    message: str
    type: NotificationType = NotificationType.EMAIL
    subject: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class NotificationResponse(BaseModel):
    id: str
    status: NotificationStatus
    message: str
    created_at: datetime
    
class NotificationStatusResponse(BaseModel):
    id: str
    status: NotificationStatus
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
