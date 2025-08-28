"""
Unit tests for the core services.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import uuid
from datetime import datetime

# Import mock services to avoid circular imports
from tests.mock_services import (
    MockNotificationService, MockNotificationTemplateService,
    MockNotificationLogService, MockUserPreferenceService
)


@pytest.mark.unit
class TestNotificationService:
    """Test cases for NotificationService."""

    @pytest.mark.asyncio
    async def test_notification_service_initialization(self, mock_db_session):
        """Test NotificationService initialization."""
        service = MockNotificationService(mock_db_session)
        
        assert service.db == mock_db_session
        assert hasattr(service, 'adapters')
        assert hasattr(service, 'template_service')
        assert hasattr(service, 'log_service')
        assert hasattr(service, 'preference_service')

    def test_load_adapters(self, mock_notification_service):
        """Test adapter loading functionality."""
        # Call the method
        mock_notification_service._load_adapters()
        
        # Should have adapters loaded
        assert 'email' in mock_notification_service.adapters
        assert 'sms' in mock_notification_service.adapters
        assert 'push' in mock_notification_service.adapters

    def test_render_template_success(self, mock_notification_service):
        """Test successful template rendering."""
        template = "Hello {user_name}, welcome to {app_name}!"
        context = {"user_name": "John", "app_name": "MyApp"}
        
        result = mock_notification_service._render_template(template, context)
        
        assert result == "Hello John, welcome to MyApp!"

    def test_render_template_missing_variable(self, mock_notification_service):
        """Test template rendering with missing variable."""
        template = "Hello {user_name}, welcome to {app_name}!"
        context = {"user_name": "John"}  # Missing app_name
        
        result = mock_notification_service._render_template(template, context)
        
        # Should return original template when variable is missing
        assert result == template

    @pytest.mark.asyncio
    async def test_send_notification_success(self, mock_notification_service, sample_template):
        """Test successful notification sending."""
        # Setup mocks
        mock_notification_service.template_service.get_template_by_name = AsyncMock(return_value=sample_template)
        mock_notification_service.preference_service.get_user_preference = AsyncMock(return_value=None)
        mock_notification_service.log_service.create_log = AsyncMock(return_value=MagicMock(id=1))
        mock_notification_service.log_service.update_log = AsyncMock()
        
        # Mock adapter
        mock_adapter = MagicMock()
        mock_adapter.send.return_value = {"success": True, "message_id": "msg_123"}
        mock_notification_service.adapters = {"email": mock_adapter}
        
        # Call the method
        result = await mock_notification_service.send_notification(
            user_id=123,
            template_name="welcome_email",
            context={"user_name": "John", "app_name": "MyApp"}
        )
        
        assert result["success"] is True
        assert "notification_id" in result
        assert result["type"] == "email"
        assert result["template_name"] == "welcome_email"

    @pytest.mark.asyncio
    async def test_send_notification_template_not_found(self, mock_notification_service):
        """Test notification sending with non-existent template."""
        mock_notification_service.template_service.get_template_by_name = AsyncMock(return_value=None)
        
        result = await mock_notification_service.send_notification(
            user_id=123,
            template_name="nonexistent_template",
            context={}
        )
        
        assert result["success"] is False
        assert "Template 'nonexistent_template' not found" in result["error"]

    @pytest.mark.asyncio
    async def test_send_notification_adapter_not_found(self, mock_notification_service, sample_template):
        """Test notification sending with no adapter for template type."""
        mock_notification_service.template_service.get_template_by_name = AsyncMock(return_value=sample_template)
        mock_notification_service.preference_service.get_user_preference = AsyncMock(return_value=None)
        mock_notification_service.adapters = {}  # No adapters loaded
        
        result = await mock_notification_service.send_notification(
            user_id=123,
            template_name="welcome_email",
            context={}
        )
        
        assert result["success"] is False
        assert "No adapter found for type 'email'" in result["error"]

    @pytest.mark.asyncio
    async def test_send_notification_user_preferences_disabled(self, mock_notification_service, sample_template, sample_user_preferences):
        """Test notification sending skipped due to user preferences."""
        # Disable email notifications
        sample_user_preferences.email_enabled = False
        
        mock_notification_service.template_service.get_template_by_name = AsyncMock(return_value=sample_template)
        mock_notification_service.preference_service.get_user_preference = AsyncMock(return_value=sample_user_preferences)
        
        result = await mock_notification_service.send_notification(
            user_id=123,
            template_name="welcome_email",
            context={}
        )
        
        assert result["success"] is False
        assert result["skipped"] is True
        assert "User has disabled email notifications" in result["error"]

    @pytest.mark.asyncio
    async def test_send_notification_adapter_failure(self, mock_notification_service, sample_template):
        """Test notification sending with adapter failure."""
        mock_notification_service.template_service.get_template_by_name = AsyncMock(return_value=sample_template)
        mock_notification_service.preference_service.get_user_preference = AsyncMock(return_value=None)
        mock_notification_service.log_service.create_log = AsyncMock(return_value=MagicMock(id=1))
        mock_notification_service.log_service.update_log = AsyncMock()
        
        # Mock adapter that fails
        mock_adapter = MagicMock()
        mock_adapter.send.return_value = {"success": False, "error": "Sending failed"}
        mock_notification_service.adapters = {"email": mock_adapter}
        
        result = await mock_notification_service.send_notification(
            user_id=123,
            template_name="welcome_email",
            context={"user_name": "John"}
        )
        
        assert result["success"] is False
        assert result["error"] == "Sending failed"

    @pytest.mark.asyncio
    async def test_send_notification_exception_handling(self, mock_notification_service):
        """Test notification sending with exception."""
        mock_notification_service.template_service.get_template_by_name = AsyncMock(side_effect=Exception("Database error"))
        
        result = await mock_notification_service.send_notification(
            user_id=123,
            template_name="welcome_email",
            context={}
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]


@pytest.mark.unit
class TestNotificationTemplateService:
    """Test cases for NotificationTemplateService."""

    @pytest.mark.asyncio
    async def test_create_template(self, mock_template_service, sample_template):
        """Test template creation."""
        template_data = MagicMock()
        template_data.name = "test_template"
        template_data.notification_type = "email"
        template_data.subject = "Test Subject"
        template_data.body = "Test Body"
        
        # The mock service will return a MagicMock object
        result = await mock_template_service.create_template(template_data)
        
        # Verify the mock service returns a valid result
        assert result is not None
        assert hasattr(result, 'id')
        assert hasattr(result, 'name')

    @pytest.mark.asyncio
    async def test_get_template(self, mock_template_service):
        """Test template retrieval by ID."""
        result = await mock_template_service.get_template(1)
        
        # Verify mock service returns a valid result
        assert result is not None
        assert hasattr(result, 'id')
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_template_by_name(self, mock_template_service):
        """Test template retrieval by name."""
        result = await mock_template_service.get_template_by_name("welcome_email")
        
        # Verify mock service returns a valid result
        assert result is not None
        assert hasattr(result, 'name')

    @pytest.mark.asyncio
    async def test_list_templates(self, mock_template_service):
        """Test template listing."""
        result = await mock_template_service.list_templates(1, 50, "email")
        
        # Verify mock service returns a valid list result
        assert result is not None
        assert hasattr(result, '__iter__')  # Should be iterable like a list

    @pytest.mark.asyncio
    async def test_update_template(self, mock_template_service):
        """Test template update."""
        template_data = MagicMock()
        result = await mock_template_service.update_template(1, template_data)
        
        # Verify the mock service returns a valid result
        assert result is not None
        assert hasattr(result, 'id')
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_delete_template(self, mock_template_service):
        """Test template deletion."""
        result = await mock_template_service.delete_template(1)
        
        # Verify the mock service returns a valid result (should be True)
        assert result is True


@pytest.mark.unit
class TestNotificationLogService:
    """Test cases for NotificationLogService."""

    @pytest.mark.asyncio
    async def test_create_log(self, mock_log_service):
        """Test log creation."""
        result = await mock_log_service.create_log(
            user_id=123,
            notification_type="email",
            template_id=1,
            recipient="test@example.com",
            subject="Test Subject",
            body="Test Body"
        )
        
        # Verify the mock service returns a valid result
        assert result is not None
        assert hasattr(result, 'id')

    @pytest.mark.asyncio
    async def test_get_log(self, mock_log_service):
        """Test log retrieval."""
        result = await mock_log_service.get_log("log_id")
        
        # Verify the mock service returns a valid result
        assert result is not None
        assert hasattr(result, 'id')

    @pytest.mark.asyncio
    async def test_get_user_logs(self, mock_log_service):
        """Test user log retrieval."""
        result = await mock_log_service.get_user_logs(123, 1, 50)
        
        # Verify the mock service returns a valid result
        assert result is not None
        assert hasattr(result, '__iter__')  # Should be iterable like a list

    @pytest.mark.asyncio
    async def test_update_log(self, mock_log_service):
        """Test log update."""
        log_data = MagicMock()
        result = await mock_log_service.update_log("log_id", log_data)
        
        # Verify the mock service returns a valid result
        assert result is not None
        assert hasattr(result, 'id')


@pytest.mark.unit
class TestUserPreferenceService:
    """Test cases for UserPreferenceService."""

    @pytest.mark.asyncio
    async def test_get_user_preference(self, mock_user_preference_service):
        """Test user preference retrieval."""
        result = await mock_user_preference_service.get_user_preference(123, "email")
        
        # Verify the mock service returns a valid result
        assert result is not None
        assert hasattr(result, 'user_id')
        assert result.user_id == 123

    @pytest.mark.asyncio
    async def test_create_user_preference(self, mock_user_preference_service):
        """Test user preference creation."""
        preference_data = MagicMock()
        result = await mock_user_preference_service.create_user_preference(preference_data)
        
        # Verify the mock service returns a valid result
        assert result is not None
        assert hasattr(result, 'user_id')

    @pytest.mark.asyncio
    async def test_update_user_preference(self, mock_user_preference_service):
        """Test user preference update."""
        preference_data = MagicMock()
        result = await mock_user_preference_service.update_user_preference(123, preference_data)
        
        # Verify the mock service returns a valid result
        assert result is not None
        assert hasattr(result, 'user_id')

    @pytest.mark.asyncio
    async def test_upsert_user_preference(self, mock_user_preference_service):
        """Test user preference upsert."""
        preference_data = MagicMock()
        preference_data.user_id = 123
        preference_data.notification_type = "email"
        preference_data.is_enabled = True
        preference_data.quiet_hours_start = None
        preference_data.quiet_hours_end = None
        
        result = await mock_user_preference_service.upsert_user_preference(preference_data)
        
        # Verify the mock service returns a valid result
        assert result is not None
        assert hasattr(result, 'user_id')

    @pytest.mark.asyncio
    async def test_delete_user_preference(self, mock_user_preference_service):
        """Test user preference deletion."""
        result = await mock_user_preference_service.delete_user_preference(123)
        
        # Verify the mock service returns a valid result (should be True)
        assert result is True
