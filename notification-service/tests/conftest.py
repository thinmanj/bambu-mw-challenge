"""
Test configuration and fixtures for the notification service tests.
"""

import asyncio
import pytest
import os
import sys
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, time
from typing import Dict, Any, Generator, AsyncGenerator

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# NOTE: Removed SQLAlchemy mocking as it was causing import conflicts
# The real SQLAlchemy module works fine in tests

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session

@pytest.fixture
def mock_redis_client():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.hset = AsyncMock()
    redis.hget = AsyncMock()
    redis.ping = AsyncMock()
    return redis

@pytest.fixture
def sample_notification_request():
    """Sample notification request data."""
    return {
        "user_id": 123,
        "template_name": "welcome_email",
        "context": {
            "user_name": "John Doe",
            "app_name": "MyBambu",
            "to_email": "john.doe@example.com"
        }
    }

@pytest.fixture
def sample_template():
    """Sample notification template."""
    template = MagicMock()
    template.id = 1
    template.name = "welcome_email"
    template.subject = "Welcome to {app_name}"
    template.body = "Hello {user_name}, welcome to {app_name}!"
    template.notification_type = "email"
    template.variables = {"user_name": "string", "app_name": "string"}
    template.created_at = datetime.now()
    template.updated_at = datetime.now()
    return template

@pytest.fixture
def sample_notification_log():
    """Sample notification log."""
    # Create a proper mock object with valid enum values
    from unittest.mock import MagicMock
    from datetime import datetime
    
    log = MagicMock()
    log.id = 1  # Use integer ID as expected by schema
    log.user_id = 123
    log.template_id = 1
    log.type = "email"  # Valid enum value
    log.status = "pending"  # Valid enum value
    log.created_at = datetime.now()
    log.sent_at = None
    log.error_message = None
    log.notification_metadata = {}  # Valid dict
    
    # Create mock template
    template = MagicMock()
    template.id = 1
    template.name = "welcome_email"
    template.subject = "Welcome to Test App"
    template.body = "Welcome {user_name}!"
    template.type = "email"  # Valid enum value
    template.variables = {"user_name": "string"}  # Valid dict
    template.created_at = datetime.now()
    template.updated_at = datetime.now()
    
    log.template = template
    
    return log

@pytest.fixture
def sample_user_preferences():
    """Sample user preferences."""
    prefs = MagicMock()
    prefs.id = 1
    prefs.user_id = 123
    prefs.notification_type = "email"
    prefs.is_enabled = False  # Set to False to test disabled preference case
    prefs.quiet_hours_start = time(22, 0)
    prefs.quiet_hours_end = time(8, 0)
    prefs.created_at = datetime.now()
    prefs.updated_at = datetime.now()
    return prefs

@pytest.fixture
def email_adapter():
    """Email adapter instance."""
    from adapters.email import EmailProvider
    return EmailProvider()

@pytest.fixture
def sms_adapter():
    """SMS adapter instance."""
    from adapters.sms import SMSProvider
    return SMSProvider()

@pytest.fixture
def push_adapter():
    """Push adapter instance."""
    from adapters.push import PushProvider
    return PushProvider()

@pytest.fixture
def mock_notification_service(mock_db_session):
    """Mock notification service."""
    from tests.mock_services import MockNotificationService
    service = MockNotificationService(mock_db_session)
    return service

@pytest.fixture
def mock_template_service(mock_db_session):
    """Mock notification template service."""
    from tests.mock_services import MockNotificationTemplateService
    service = MockNotificationTemplateService(mock_db_session)
    return service

@pytest.fixture
def mock_log_service(mock_db_session):
    """Mock notification log service."""
    from tests.mock_services import MockNotificationLogService
    service = MockNotificationLogService(mock_db_session)
    return service

@pytest.fixture
def mock_user_preference_service(mock_db_session):
    """Mock user preference service."""
    from tests.mock_services import MockUserPreferenceService
    service = MockUserPreferenceService(mock_db_session)
    return service

@pytest.fixture
def mock_fastapi_app():
    """Mock FastAPI application."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    
    # Create a minimal app for testing
    app = FastAPI(title="Test App")
    
    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok"}
    
    return TestClient(app)

@pytest.fixture
def email_context():
    """Sample email context."""
    return {
        "to_email": "test@example.com",
        "subject": "Test Subject",
        "body": "Test message body"
    }

@pytest.fixture
def sms_context():
    """Sample SMS context."""
    return {
        "phone_number": "+1234567890",
        "message": "Test SMS message"
    }

@pytest.fixture
def push_context():
    """Sample push notification context."""
    return {
        "device_token": "test_device_token_123",
        "title": "Test Push",
        "message": "Test push notification message"
    }

@pytest.fixture
def invalid_email_context():
    """Invalid email context (missing required fields)."""
    return {
        "subject": "Test Subject",
        "body": "Test message body"
        # Missing to_email
    }

@pytest.fixture
def invalid_sms_context():
    """Invalid SMS context (missing required fields)."""
    return {
        "message": "Test SMS message"
        # Missing phone_number
    }

@pytest.fixture
def invalid_push_context():
    """Invalid push context (missing required fields)."""
    return {
        "title": "Test Push"
        # Missing device_token and message
    }

# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict(os.environ, {
        'DATABASE_URL': 'sqlite:///:memory:',
        'REDIS_URL': 'redis://localhost:6379',
        'PORT': '8003',
        'TESTING': 'true'
    }):
        yield

# Health check fixtures
@pytest.fixture
def mock_health_dependencies():
    """Mock health check dependencies."""
    with patch('database.connection.get_engine') as mock_engine, \
         patch('database.connection.get_redis_client') as mock_redis:
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_conn.execute.return_value.fetchone.return_value = [1]
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn
        
        # Mock Redis connection
        mock_redis_client = AsyncMock()
        mock_redis_client.ping = AsyncMock(return_value=True)
        mock_redis.return_value = mock_redis_client
        
        yield {
            'engine': mock_engine,
            'redis': mock_redis,
            'redis_client': mock_redis_client
        }
