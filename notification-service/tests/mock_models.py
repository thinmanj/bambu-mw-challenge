"""
Mock models for testing without SQLAlchemy dependency issues.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
from unittest.mock import Mock


class NotificationType(str, Enum):
    """Mock notification types."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationStatus(str, Enum):
    """Mock notification statuses."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


@dataclass
class MockNotificationTemplate:
    """Mock notification template."""
    id: int
    name: str
    notification_type: NotificationType
    subject: Optional[str] = None
    body: str = ""
    is_active: bool = True
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


@dataclass 
class MockNotificationLog:
    """Mock notification log."""
    id: int
    user_id: str
    notification_type: NotificationType
    template_id: Optional[int] = None
    recipient: str = ""
    subject: Optional[str] = None
    body: str = ""
    status: NotificationStatus = NotificationStatus.PENDING
    external_message_id: Optional[str] = None
    error_message: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


@dataclass
class MockUserPreference:
    """Mock user preference."""
    id: int
    user_id: str
    notification_type: NotificationType
    is_enabled: bool = True
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


# Mock database session
class MockAsyncSession:
    """Mock async database session."""
    
    def __init__(self):
        self.queries = []
        self.commits = []
        self.rollbacks = []
        
    async def execute(self, query):
        """Mock execute method."""
        self.queries.append(query)
        return Mock()
        
    async def commit(self):
        """Mock commit method.""" 
        self.commits.append(datetime.now())
        
    async def rollback(self):
        """Mock rollback method."""
        self.rollbacks.append(datetime.now())
        
    async def close(self):
        """Mock close method."""
        pass
        
    def add(self, instance):
        """Mock add method."""
        pass
        
    async def refresh(self, instance):
        """Mock refresh method."""
        pass


# Patch core.models to use mock models
import sys
from unittest.mock import MagicMock

# Create a mock module for core.models
mock_core_models = MagicMock()
mock_core_models.NotificationType = NotificationType
mock_core_models.NotificationStatus = NotificationStatus
mock_core_models.NotificationTemplate = MockNotificationTemplate
mock_core_models.NotificationLog = MockNotificationLog
mock_core_models.UserPreference = MockUserPreference

sys.modules['core.models'] = mock_core_models

# Create mock database connection module
mock_db_connection = MagicMock()
mock_db_connection.get_session = lambda: MockAsyncSession()
mock_db_connection.get_redis_client = lambda: Mock()
mock_db_connection.get_engine = lambda: Mock()

sys.modules['database.connection'] = mock_db_connection
