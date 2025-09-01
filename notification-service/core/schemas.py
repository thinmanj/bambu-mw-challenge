"""
Core schemas for data operations.
These schemas are used by repositories and services to avoid circular imports.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, time

# These enums should be defined in core to avoid circular imports
from enum import Enum


class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


# Repository level create/update schemas
class NotificationTemplateCreate(BaseModel):
    name: str = Field(..., max_length=100, description="Template name")
    subject: Optional[str] = Field(None, max_length=255, description="Template subject")
    body: str = Field(..., description="Template body content")
    type: str = Field(..., description="Notification type")  # Using str to avoid enum import issues
    variables: Optional[Dict[str, Any]] = Field(None, description="Template variables")


class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100, description="Template name")
    subject: Optional[str] = Field(None, max_length=255, description="Template subject")
    body: Optional[str] = Field(None, description="Template body content")
    type: Optional[str] = Field(None, description="Notification type")
    variables: Optional[Dict[str, Any]] = Field(None, description="Template variables")


class NotificationLogCreate(BaseModel):
    user_id: int = Field(..., description="User ID")
    template_id: Optional[int] = Field(None, description="Template ID")
    type: str = Field(..., description="Notification type")
    status: str = Field("pending", description="Notification status")
    sent_at: Optional[datetime] = Field(None, description="When notification was sent")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    notification_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class NotificationLogUpdate(BaseModel):
    status: Optional[str] = Field(None, description="Notification status")
    sent_at: Optional[datetime] = Field(None, description="When notification was sent")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    notification_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class UserPreferenceCreate(BaseModel):
    user_id: int = Field(..., description="User ID")
    email_enabled: bool = Field(True, description="Email notifications enabled")
    sms_enabled: bool = Field(True, description="SMS notifications enabled")
    push_enabled: bool = Field(True, description="Push notifications enabled")
    quiet_hours_start: Optional[time] = Field(None, description="Quiet hours start time")
    quiet_hours_end: Optional[time] = Field(None, description="Quiet hours end time")


class UserPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = Field(None, description="Email notifications enabled")
    sms_enabled: Optional[bool] = Field(None, description="SMS notifications enabled")
    push_enabled: Optional[bool] = Field(None, description="Push notifications enabled")
    quiet_hours_start: Optional[time] = Field(None, description="Quiet hours start time")
    quiet_hours_end: Optional[time] = Field(None, description="Quiet hours end time")
