from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, time
from api.v1.enums import NotificationType, NotificationStatus


# Base schemas with common configuration
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# API Request/Response Models (not stored in DB)
class NotificationRequest(BaseModel):
    user_id: int = Field(..., description="User ID who will receive the notification")
    template_name: str = Field(..., description="Name of the notification template to use")
    context: Dict[str, Any] = Field(..., description="Template variables/context for rendering")

class NotificationResponse(BaseModel):
    id: int
    status: NotificationStatus
    message: str
    created_at: datetime

class SendNotificationResponse(BaseModel):
    success: bool
    notification_id: str
    message: Optional[str] = None
    error: Optional[str] = None
    type: Optional[str] = None
    template_name: Optional[str] = None
    skipped: Optional[bool] = False


# Notification Template Schemas
class NotificationTemplateBase(BaseModel):
    name: str = Field(..., max_length=100, description="Template name")
    subject: Optional[str] = Field(None, max_length=255, description="Template subject")
    body: str = Field(..., description="Template body content")
    type: NotificationType = Field(..., description="Notification type")
    variables: Optional[Dict[str, Any]] = Field(None, description="Template variables")


class NotificationTemplateCreate(NotificationTemplateBase):
    pass


class NotificationTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100, description="Template name")
    subject: Optional[str] = Field(None, max_length=255, description="Template subject")
    body: Optional[str] = Field(None, description="Template body content")
    type: Optional[NotificationType] = Field(None, description="Notification type")
    variables: Optional[Dict[str, Any]] = Field(None, description="Template variables")


class NotificationTemplate(NotificationTemplateBase, BaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime


# Notification Log Schemas
class NotificationLogBase(BaseModel):
    user_id: int = Field(..., description="User ID")
    template_id: Optional[int] = Field(None, description="Template ID")
    type: NotificationType = Field(..., description="Notification type")
    status: NotificationStatus = Field(NotificationStatus.PENDING, description="Notification status")
    sent_at: Optional[datetime] = Field(None, description="When notification was sent")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    notification_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class NotificationLogCreate(BaseModel):
    id: Optional[str] = Field(None, description="Notification ID")
    user_id: int = Field(..., description="User ID")
    template_name: str = Field(..., description="Template name")
    notification_type: str = Field(..., description="Notification type")
    status: NotificationStatus = Field(NotificationStatus.PENDING, description="Notification status")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    template_id: Optional[int] = Field(None, description="Template ID")
    sent_at: Optional[datetime] = Field(None, description="When notification was sent")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    response_data: Optional[Dict[str, Any]] = Field(None, description="Response data from provider")


class NotificationLogUpdate(BaseModel):
    status: Optional[NotificationStatus] = Field(None, description="Notification status")
    sent_at: Optional[datetime] = Field(None, description="When notification was sent")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    notification_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    response_data: Optional[Dict[str, Any]] = Field(None, description="Response data from provider")


class NotificationLog(NotificationLogBase, BaseSchema):
    id: int
    created_at: datetime
    template: Optional[NotificationTemplate] = None


# User Preference Schemas
class UserPreferenceBase(BaseModel):
    user_id: int = Field(..., description="User ID")
    email_enabled: bool = Field(True, description="Email notifications enabled")
    sms_enabled: bool = Field(True, description="SMS notifications enabled")
    push_enabled: bool = Field(True, description="Push notifications enabled")
    quiet_hours_start: Optional[time] = Field(None, description="Quiet hours start time")
    quiet_hours_end: Optional[time] = Field(None, description="Quiet hours end time")


class UserPreferenceCreate(UserPreferenceBase):
    pass


class UserPreferenceUpdate(BaseModel):
    email_enabled: Optional[bool] = Field(None, description="Email notifications enabled")
    sms_enabled: Optional[bool] = Field(None, description="SMS notifications enabled")
    push_enabled: Optional[bool] = Field(None, description="Push notifications enabled")
    quiet_hours_start: Optional[time] = Field(None, description="Quiet hours start time")
    quiet_hours_end: Optional[time] = Field(None, description="Quiet hours end time")


class UserPreference(UserPreferenceBase, BaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime


# List response schemas
class PaginatedResponse(BaseModel):
    total: int
    page: int = 1
    size: int = 50
    pages: int


class NotificationTemplateList(PaginatedResponse):
    items: List[NotificationTemplate]


class NotificationLogList(PaginatedResponse):
    items: List[NotificationLog]


class UserPreferenceList(PaginatedResponse):
    items: List[UserPreference]
