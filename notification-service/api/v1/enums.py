"""
Independent enums for API schemas to avoid circular imports.
"""
from enum import Enum


class NotificationType(str, Enum):
    """Notification types."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationStatus(str, Enum):
    """Notification status values."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"
