"""
GraphQL Types for Notification Service

This module defines all GraphQL types using Strawberry GraphQL for the notification service.
"""
import strawberry
from typing import Optional, List, Dict, Any
from datetime import datetime, time
from enum import Enum


@strawberry.enum
class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


@strawberry.enum
class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


@strawberry.type
class NotificationTemplate:
    id: int
    name: str
    subject: Optional[str]
    body: str
    type: NotificationType
    variables: Optional[str] = None  # JSON string for GraphQL compatibility
    created_at: datetime
    updated_at: datetime


@strawberry.type
class NotificationLog:
    id: int
    user_id: int
    template_id: Optional[int]
    type: NotificationType
    status: NotificationStatus
    sent_at: Optional[datetime]
    error_message: Optional[str]
    metadata: Optional[str] = None  # JSON string for GraphQL compatibility
    created_at: datetime
    template: Optional[NotificationTemplate] = None


@strawberry.type
class UserPreference:
    id: int
    user_id: int
    email_enabled: bool
    sms_enabled: bool
    push_enabled: bool
    quiet_hours_start: Optional[str] = None  # Time as string for GraphQL compatibility
    quiet_hours_end: Optional[str] = None  # Time as string for GraphQL compatibility
    created_at: datetime
    updated_at: datetime


@strawberry.type
class NotificationResponse:
    id: int
    status: NotificationStatus
    message: str
    created_at: datetime


@strawberry.type
class PaginationInfo:
    total: int
    page: int
    size: int
    pages: int


@strawberry.type
class NotificationTemplateList:
    items: List[NotificationTemplate]
    pagination: PaginationInfo


@strawberry.type
class NotificationLogList:
    items: List[NotificationLog]
    pagination: PaginationInfo


# Input Types for Mutations
@strawberry.input
class NotificationRequestInput:
    user_id: int
    template_name: str
    context: str  # JSON string for GraphQL compatibility


@strawberry.input
class NotificationTemplateCreateInput:
    name: str
    subject: Optional[str] = None
    body: str
    type: NotificationType
    variables: Optional[str] = None  # JSON string


@strawberry.input
class NotificationTemplateUpdateInput:
    name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    type: Optional[NotificationType] = None
    variables: Optional[str] = None  # JSON string


@strawberry.input
class NotificationLogUpdateInput:
    status: Optional[NotificationStatus] = None
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[str] = None  # JSON string


@strawberry.input
class UserPreferenceUpdateInput:
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None  # Time as string
    quiet_hours_end: Optional[str] = None  # Time as string


# Query Input Types
@strawberry.input
class PaginationInput:
    page: int = 1
    size: int = 50


@strawberry.input
class TemplateFilterInput:
    type_filter: Optional[str] = None
    pagination: Optional[PaginationInput] = None
