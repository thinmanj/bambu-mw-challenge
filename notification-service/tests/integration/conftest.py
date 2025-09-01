"""
Fixtures for integration tests.
"""

import pytest
from datetime import datetime, time
from unittest.mock import MagicMock


@pytest.fixture
def sample_notification_request():
    """Sample notification request data for testing."""
    return {
        "user_id": 123,
        "template_name": "welcome_email",
        "context": {
            "name": "John Doe",
            "email": "john@example.com",
            "company": "Test Corp"
        }
    }


class MockTemplate:
    """Mock template class for testing."""
    def __init__(self):
        self.id = 1
        self.name = "welcome_email"
        self.subject = "Welcome to {company}"
        self.body = "Hello {name}, welcome to {company}!"
        self.type = "email"
        self.variables = {"name": "string", "company": "string"}
        self.created_at = datetime(2024, 12, 27, 9, 0, 0)
        self.updated_at = datetime(2024, 12, 27, 9, 0, 0)


class MockNotificationLog:
    """Mock notification log class for testing."""
    def __init__(self):
        self.id = 1
        self.user_id = 123
        self.template_id = 1
        self.type = "email"
        self.status = "sent"
        self.sent_at = datetime(2024, 12, 27, 10, 30, 0)
        self.error_message = None
        self.notification_metadata = {
            "recipient": "john@example.com",
            "subject": "Welcome to Test Corp"
        }
        self.created_at = datetime(2024, 12, 27, 10, 0, 0)
        self.template = MockTemplate()


@pytest.fixture
def sample_notification_log():
    """Sample notification log object for testing."""
    return MockNotificationLog()


@pytest.fixture
def sample_user_preference():
    """Sample user preference object for testing."""
    mock_preference = MagicMock()
    mock_preference.id = 1
    mock_preference.user_id = 123
    mock_preference.email_enabled = True
    mock_preference.sms_enabled = True
    mock_preference.push_enabled = False
    mock_preference.quiet_hours_start = time(22, 0)
    mock_preference.quiet_hours_end = time(8, 0)
    mock_preference.created_at = datetime(2024, 12, 27, 9, 0, 0)
    mock_preference.updated_at = datetime(2024, 12, 27, 9, 0, 0)
    
    return mock_preference


@pytest.fixture
def sample_notification_template():
    """Sample notification template object for testing."""
    mock_template = MagicMock()
    mock_template.id = 1
    mock_template.name = "welcome_email"
    mock_template.subject = "Welcome to {company}"
    mock_template.body = "Hello {name}, welcome to {company}!"
    mock_template.type = "email"
    mock_template.variables = {"name": "string", "company": "string"}
    mock_template.created_at = datetime(2024, 12, 27, 9, 0, 0)
    mock_template.updated_at = datetime(2024, 12, 27, 9, 0, 0)
    
    return mock_template
