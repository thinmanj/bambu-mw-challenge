from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime, time
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Time, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from database.connection import Base


# Pydantic Enums
class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


# SQLAlchemy Database Models
class NotificationTemplate(Base):
    """Notification template model"""
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    type = Column(String(20), nullable=False)
    variables = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    notification_logs = relationship("NotificationLog", back_populates="template")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("type IN ('email', 'sms', 'push')", name='check_notification_template_type'),
    )


class NotificationLog(Base):
    """Notification log model"""
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    template_id = Column(Integer, ForeignKey("notification_templates.id"), nullable=True)
    type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default='pending')
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    template = relationship("NotificationTemplate", back_populates="notification_logs")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("type IN ('email', 'sms', 'push')", name='check_notification_log_type'),
        CheckConstraint("status IN ('pending', 'sent', 'failed', 'bounced')", name='check_notification_log_status'),
    )


class UserPreference(Base):
    """User notification preferences model"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    quiet_hours_start = Column(Time, nullable=True)
    quiet_hours_end = Column(Time, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


