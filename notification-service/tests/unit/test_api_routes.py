"""
Comprehensive unit tests for API routes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException, status
import json

from api.v1.routes import notifications_router, templates_router, preferences_router
from api.v1.schemas import (
    NotificationRequest, SendNotificationResponse,
    NotificationTemplateCreate, NotificationTemplateUpdate,
    NotificationLogUpdate, UserPreferenceCreate, UserPreferenceUpdate,
    NotificationTemplate, NotificationLog, UserPreference,
    NotificationTemplateList, NotificationLogList
)
from core.models import NotificationStatus


@pytest.fixture
def mock_notification_service():
    """Mock notification service."""
    return AsyncMock()


@pytest.fixture
def mock_template_service():
    """Mock template service."""
    return AsyncMock()


@pytest.fixture
def mock_log_service():
    """Mock log service."""
    return AsyncMock()


@pytest.fixture
def mock_preference_service():
    """Mock preference service."""
    return AsyncMock()


@pytest.mark.unit
class TestNotificationsRouter:
    """Test cases for notifications router."""

    @pytest.mark.asyncio
    async def test_send_notification_success(self, mock_notification_service):
        """Test successful notification sending."""
        # Mock service response
        mock_notification_service.send_notification.return_value = {
            "success": True,
            "notification_id": "12345",
            "type": "email",
            "template_name": "welcome"
        }
        
        request = NotificationRequest(
            user_id=123,
            template_name="welcome",
            context={"name": "John"}
        )
        
        # Import and test the route function directly
        from api.v1.routes import send_notification
        response = await send_notification(request, mock_notification_service)
        
        assert isinstance(response, SendNotificationResponse)
        assert response.success is True
        assert response.notification_id == "12345"
        assert response.type == "email"
        assert response.template_name == "welcome"
        assert response.skipped is False
        assert "sent" in response.message
        
        mock_notification_service.send_notification.assert_called_once_with(
            user_id=123,
            template_name="welcome",
            context={"name": "John"}
        )

    @pytest.mark.asyncio
    async def test_send_notification_failure(self, mock_notification_service):
        """Test notification sending failure."""
        mock_notification_service.send_notification.return_value = {
            "success": False,
            "notification_id": "12345",
            "error": "SMTP server unreachable",
            "type": "email",
            "template_name": "welcome"
        }
        
        request = NotificationRequest(
            user_id=123,
            template_name="welcome",
            context={"name": "John"}
        )
        
        from api.v1.routes import send_notification
        response = await send_notification(request, mock_notification_service)
        
        assert isinstance(response, SendNotificationResponse)
        assert response.success is False
        assert response.notification_id == "12345"
        assert response.error == "SMTP server unreachable"
        assert response.skipped is False
        assert "failed" in response.message

    @pytest.mark.asyncio
    async def test_send_notification_skipped(self, mock_notification_service):
        """Test notification skipped due to user preferences."""
        mock_notification_service.send_notification.return_value = {
            "success": False,
            "notification_id": "12345",
            "error": "User has disabled email notifications",
            "skipped": True,
            "type": "email",
            "template_name": "welcome"
        }
        
        request = NotificationRequest(
            user_id=123,
            template_name="welcome",
            context={"name": "John"}
        )
        
        from api.v1.routes import send_notification
        response = await send_notification(request, mock_notification_service)
        
        assert isinstance(response, SendNotificationResponse)
        assert response.success is False
        assert response.skipped is True
        assert "skipped" in response.message

    @pytest.mark.asyncio
    async def test_send_notification_service_exception(self, mock_notification_service):
        """Test notification sending with service exception."""
        mock_notification_service.send_notification.side_effect = Exception("Database error")
        
        request = NotificationRequest(
            user_id=123,
            template_name="welcome",
            context={"name": "John"}
        )
        
        from api.v1.routes import send_notification
        
        with pytest.raises(HTTPException) as exc_info:
            await send_notification(request, mock_notification_service)
        
        assert exc_info.value.status_code == 500
        assert "Database error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_notification_details_success(self, mock_log_service):
        """Test getting notification details successfully."""
        mock_notification = MagicMock(spec=NotificationLog)
        mock_notification.id = 1
        mock_notification.user_id = 123
        mock_log_service.get_log.return_value = mock_notification
        
        from api.v1.routes import get_notification_details
        response = await get_notification_details(1, mock_log_service)
        
        assert response == mock_notification
        mock_log_service.get_log.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_notification_details_not_found(self, mock_log_service):
        """Test getting notification details when not found."""
        mock_log_service.get_log.return_value = None
        
        from api.v1.routes import get_notification_details
        
        with pytest.raises(HTTPException) as exc_info:
            await get_notification_details(1, mock_log_service)
        
        assert exc_info.value.status_code == 404
        assert "Notification not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_notification_details_service_error(self, mock_log_service):
        """Test getting notification details with service error."""
        mock_log_service.get_log.side_effect = Exception("Database error")
        
        from api.v1.routes import get_notification_details
        
        with pytest.raises(HTTPException) as exc_info:
            await get_notification_details(1, mock_log_service)
        
        assert exc_info.value.status_code == 500
        assert "Internal server error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_list_user_notifications_success(self, mock_log_service):
        """Test listing user notifications."""
        mock_logs = [MagicMock(spec=NotificationLog) for _ in range(3)]
        mock_log_list = NotificationLogList(
            items=mock_logs,
            total=10,
            page=2,
            size=3,
            pages=4
        )
        mock_log_service.get_user_logs.return_value = mock_log_list
        
        from api.v1.routes import list_user_notifications
        response = await list_user_notifications(123, 2, 3, mock_log_service)
        
        assert response == mock_log_list
        mock_log_service.get_user_logs.assert_called_once_with(123, 2, 3)

    @pytest.mark.asyncio
    async def test_update_notification_status_success(self, mock_log_service):
        """Test updating notification status successfully."""
        mock_notification = MagicMock(spec=NotificationLog)
        mock_log_service.update_log.return_value = mock_notification
        
        update_data = NotificationLogUpdate(status="sent")
        
        from api.v1.routes import update_notification_status
        response = await update_notification_status(update_data, 1, mock_log_service)
        
        assert response == mock_notification
        mock_log_service.update_log.assert_called_once_with(1, update_data)

    @pytest.mark.asyncio
    async def test_update_notification_status_not_found(self, mock_log_service):
        """Test updating notification status when notification not found."""
        mock_log_service.update_log.return_value = None
        
        update_data = NotificationLogUpdate(status="sent")
        
        from api.v1.routes import update_notification_status
        
        with pytest.raises(HTTPException) as exc_info:
            await update_notification_status(update_data, 1, mock_log_service)
        
        assert exc_info.value.status_code == 404
        assert "Notification not found" in str(exc_info.value.detail)


@pytest.mark.unit
class TestTemplatesRouter:
    """Test cases for templates router."""

    @pytest.mark.asyncio
    async def test_list_templates_success(self, mock_template_service):
        """Test listing templates successfully."""
        mock_templates = [MagicMock(spec=NotificationTemplate) for _ in range(2)]
        mock_template_list = NotificationTemplateList(
            items=mock_templates,
            total=5,
            page=1,
            size=2,
            pages=3
        )
        mock_template_service.list_templates.return_value = mock_template_list
        
        from api.v1.routes import list_templates
        response = await list_templates(1, 2, "email", mock_template_service)
        
        assert response == mock_template_list
        mock_template_service.list_templates.assert_called_once_with(1, 2, "email")

    @pytest.mark.asyncio
    async def test_list_templates_service_error(self, mock_template_service):
        """Test listing templates with service error."""
        mock_template_service.list_templates.side_effect = Exception("Database error")
        
        from api.v1.routes import list_templates
        
        with pytest.raises(HTTPException) as exc_info:
            await list_templates(1, 50, None, mock_template_service)
        
        assert exc_info.value.status_code == 500
        assert "Internal server error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_template_success(self, mock_template_service):
        """Test creating template successfully."""
        mock_template = MagicMock(spec=NotificationTemplate)
        mock_template.id = 1
        mock_template.name = "welcome"
        mock_template_service.create_template.return_value = mock_template
        
        template_data = NotificationTemplateCreate(
            name="welcome",
            body="Welcome to our service!",
            type="email"
        )
        
        from api.v1.routes import create_template
        response = await create_template(template_data, mock_template_service)
        
        assert response == mock_template
        mock_template_service.create_template.assert_called_once_with(template_data)

    @pytest.mark.asyncio
    async def test_create_template_unique_constraint_violation(self, mock_template_service):
        """Test creating template with unique constraint violation."""
        mock_template_service.create_template.side_effect = Exception("unique constraint")
        
        template_data = NotificationTemplateCreate(
            name="welcome",
            body="Welcome to our service!",
            type="email"
        )
        
        from api.v1.routes import create_template
        
        with pytest.raises(HTTPException) as exc_info:
            await create_template(template_data, mock_template_service)
        
        assert exc_info.value.status_code == 400
        assert "Template name already exists" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_template_service_error(self, mock_template_service):
        """Test creating template with service error."""
        mock_template_service.create_template.side_effect = Exception("Database error")
        
        template_data = NotificationTemplateCreate(
            name="welcome",
            body="Welcome to our service!",
            type="email"
        )
        
        from api.v1.routes import create_template
        
        with pytest.raises(HTTPException) as exc_info:
            await create_template(template_data, mock_template_service)
        
        assert exc_info.value.status_code == 500
        assert "Database error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_template_details_success(self, mock_template_service):
        """Test getting template details successfully."""
        mock_template = MagicMock(spec=NotificationTemplate)
        mock_template_service.get_template.return_value = mock_template
        
        from api.v1.routes import get_template_details
        response = await get_template_details(1, mock_template_service)
        
        assert response == mock_template
        mock_template_service.get_template.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_template_details_not_found(self, mock_template_service):
        """Test getting template details when not found."""
        mock_template_service.get_template.return_value = None
        
        from api.v1.routes import get_template_details
        
        with pytest.raises(HTTPException) as exc_info:
            await get_template_details(1, mock_template_service)
        
        assert exc_info.value.status_code == 404
        assert "Template not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_template_success(self, mock_template_service):
        """Test updating template successfully."""
        mock_template = MagicMock(spec=NotificationTemplate)
        mock_template_service.update_template.return_value = mock_template
        
        update_data = NotificationTemplateUpdate(subject="Updated Subject")
        
        from api.v1.routes import update_template
        response = await update_template(update_data, 1, mock_template_service)
        
        assert response == mock_template
        mock_template_service.update_template.assert_called_once_with(1, update_data)

    @pytest.mark.asyncio
    async def test_update_template_not_found(self, mock_template_service):
        """Test updating template when not found."""
        mock_template_service.update_template.return_value = None
        
        update_data = NotificationTemplateUpdate(subject="Updated Subject")
        
        from api.v1.routes import update_template
        
        with pytest.raises(HTTPException) as exc_info:
            await update_template(update_data, 1, mock_template_service)
        
        assert exc_info.value.status_code == 404
        assert "Template not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_delete_template_success(self, mock_template_service):
        """Test deleting template successfully."""
        mock_template_service.delete_template.return_value = True
        
        from api.v1.routes import delete_template
        response = await delete_template(1, mock_template_service)
        
        # Should return None for 204 status
        assert response is None
        mock_template_service.delete_template.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_template_not_found(self, mock_template_service):
        """Test deleting template when not found."""
        mock_template_service.delete_template.return_value = False
        
        from api.v1.routes import delete_template
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_template(1, mock_template_service)
        
        assert exc_info.value.status_code == 404
        assert "Template not found" in str(exc_info.value.detail)


@pytest.mark.unit
class TestPreferencesRouter:
    """Test cases for preferences router."""

    @pytest.mark.asyncio
    async def test_get_user_preferences_success(self, mock_preference_service):
        """Test getting user preferences successfully."""
        mock_preference = MagicMock(spec=UserPreference)
        mock_preference_service.get_user_preference.return_value = mock_preference
        
        # Import the route function to test it directly
        from api.v1.routes import get_user_preferences
        response = await get_user_preferences(123, mock_preference_service)
        
        assert response == mock_preference
        mock_preference_service.get_user_preference.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_get_user_preferences_creates_default_when_none(self, mock_preference_service):
        """Test getting user preferences creates default when none exist."""
        # First call returns None, second call returns created preferences
        mock_preference = MagicMock(spec=UserPreference)
        mock_preference_service.get_user_preference.return_value = None
        mock_preference_service.create_user_preference.return_value = mock_preference
        
        from api.v1.routes import get_user_preferences
        response = await get_user_preferences(123, mock_preference_service)
        
        assert response == mock_preference
        mock_preference_service.get_user_preference.assert_called_once_with(123)
        mock_preference_service.create_user_preference.assert_called_once()
        
        # Check that create was called with correct default data
        create_call_args = mock_preference_service.create_user_preference.call_args[0][0]
        assert create_call_args.user_id == 123

    @pytest.mark.asyncio
    async def test_create_user_preferences_success(self, mock_preference_service):
        """Test creating user preferences successfully."""
        mock_preference = MagicMock(spec=UserPreference)
        mock_preference_service.create_user_preference.return_value = mock_preference
        
        preference_data = UserPreferenceCreate(
            user_id=123,
            email_enabled=False
        )
        
        from api.v1.routes import create_user_preferences
        response = await create_user_preferences(preference_data, mock_preference_service)
        
        assert response == mock_preference
        mock_preference_service.create_user_preference.assert_called_once_with(preference_data)

    @pytest.mark.asyncio
    async def test_create_user_preferences_service_error(self, mock_preference_service):
        """Test creating user preferences with service error."""
        mock_preference_service.create_user_preference.side_effect = Exception("Database error")
        
        preference_data = UserPreferenceCreate(
            user_id=123,
            email_enabled=False
        )
        
        from api.v1.routes import create_user_preferences
        
        with pytest.raises(HTTPException) as exc_info:
            await create_user_preferences(preference_data, mock_preference_service)
        
        assert exc_info.value.status_code == 500
        assert "Internal server error" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_update_user_preferences_success(self, mock_preference_service):
        """Test updating user preferences successfully."""
        mock_preference = MagicMock(spec=UserPreference)
        mock_preference_service.upsert_user_preference.return_value = mock_preference
        
        preference_data = UserPreferenceUpdate(email_enabled=False)
        
        from api.v1.routes import update_user_preferences
        response = await update_user_preferences(preference_data, 123, mock_preference_service)
        
        assert response == mock_preference
        # Check that upsert was called (actual implementation uses upsert)
        mock_preference_service.upsert_user_preference.assert_called_once()
        call_args = mock_preference_service.upsert_user_preference.call_args[0]
        assert call_args[0] == 123  # user_id
        assert call_args[1].user_id == 123  # UserPreferenceCreate.user_id

    @pytest.mark.asyncio
    async def test_update_user_preferences_not_found(self, mock_preference_service):
        """Test updating user preferences when not found."""
        mock_preference_service.update_user_preference.return_value = None
        
        preference_data = UserPreferenceUpdate(email_enabled=False)
        
        from api.v1.routes import update_user_preferences
        
        with pytest.raises(HTTPException) as exc_info:
            await update_user_preferences(preference_data, 123, mock_preference_service)
        
        assert exc_info.value.status_code == 404
        assert "User preferences not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_upsert_user_preferences_success(self, mock_preference_service):
        """Test upserting user preferences successfully."""
        mock_preference = MagicMock(spec=UserPreference)
        mock_preference_service.upsert_user_preference.return_value = mock_preference
        
        preference_data = UserPreferenceCreate(
            user_id=123,
            email_enabled=False
        )
        
        from api.v1.routes import upsert_user_preferences
        response = await upsert_user_preferences(preference_data, 123, mock_preference_service)
        
        assert response == mock_preference
        mock_preference_service.upsert_user_preference.assert_called_once_with(123, preference_data)

    @pytest.mark.asyncio
    async def test_delete_user_preferences_success(self, mock_preference_service):
        """Test deleting user preferences successfully."""
        mock_preference_service.delete_user_preference.return_value = True
        
        from api.v1.routes import delete_user_preferences
        response = await delete_user_preferences(123, mock_preference_service)
        
        # Should return None for 204 status
        assert response is None
        mock_preference_service.delete_user_preference.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_delete_user_preferences_not_found(self, mock_preference_service):
        """Test deleting user preferences when not found."""
        mock_preference_service.delete_user_preference.return_value = False
        
        from api.v1.routes import delete_user_preferences
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_user_preferences(123, mock_preference_service)
        
        assert exc_info.value.status_code == 404
        assert "User preferences not found" in str(exc_info.value.detail)


@pytest.mark.unit
class TestRouteLogging:
    """Test cases for route logging functionality."""

    @pytest.mark.asyncio
    async def test_logging_notification_success(self, mock_notification_service):
        """Test that successful notifications are logged properly."""
        mock_notification_service.send_notification.return_value = {
            "success": True,
            "notification_id": "12345",
            "type": "email",
            "template_name": "welcome"
        }
        
        request = NotificationRequest(
            user_id=123,
            template_name="welcome",
            context={"name": "John"}
        )
        
        with patch('api.v1.routes.logger') as mock_logger:
            from api.v1.routes import send_notification
            await send_notification(request, mock_notification_service)
            
            # Check that appropriate log calls were made
            mock_logger.info.assert_called()
            log_calls = mock_logger.info.call_args_list
            
            # Should have info log for request and success
            assert len(log_calls) >= 2
            assert "Sending notification" in str(log_calls[0])
            assert "Notification sent successfully" in str(log_calls[1])

    @pytest.mark.asyncio 
    async def test_logging_notification_failure(self, mock_notification_service):
        """Test that failed notifications are logged properly."""
        mock_notification_service.send_notification.return_value = {
            "success": False,
            "notification_id": "12345",
            "error": "SMTP error",
            "type": "email",
            "template_name": "welcome"
        }
        
        request = NotificationRequest(
            user_id=123,
            template_name="welcome",
            context={"name": "John"}
        )
        
        with patch('api.v1.routes.logger') as mock_logger:
            from api.v1.routes import send_notification
            await send_notification(request, mock_notification_service)
            
            # Check that error log was called
            mock_logger.error.assert_called()
            error_calls = mock_logger.error.call_args_list
            assert len(error_calls) >= 1
            assert "Notification failed" in str(error_calls[0])

    @pytest.mark.asyncio
    async def test_logging_template_operations(self, mock_template_service):
        """Test that template operations are logged properly."""
        mock_template_list = NotificationTemplateList(
            items=[],
            total=5,
            page=1,
            size=50,
            pages=1
        )
        mock_template_service.list_templates.return_value = mock_template_list
        
        with patch('api.v1.routes.logger') as mock_logger:
            from api.v1.routes import list_templates
            await list_templates(1, 50, None, mock_template_service)
            
            # Check that info logs were called for listing
            mock_logger.info.assert_called()
            log_calls = mock_logger.info.call_args_list
            assert len(log_calls) >= 2
            assert "Listing templates" in str(log_calls[0])
            assert "Templates retrieved" in str(log_calls[1])


@pytest.mark.unit 
class TestRouteValidation:
    """Test cases for route input validation."""

    @pytest.mark.asyncio
    async def test_notification_request_validation(self, mock_notification_service):
        """Test that notification requests are properly validated."""
        # Test with missing required fields should be handled by pydantic
        # but we can test the service is called with correct data
        
        mock_notification_service.send_notification.return_value = {
            "success": True,
            "notification_id": "12345",
            "type": "email",
            "template_name": "welcome"
        }
        
        # Valid request
        request = NotificationRequest(
            user_id=123,
            template_name="welcome",
            context={"name": "John", "order_id": "456"}
        )
        
        from api.v1.routes import send_notification
        await send_notification(request, mock_notification_service)
        
        # Verify service was called with exact data
        mock_notification_service.send_notification.assert_called_once_with(
            user_id=123,
            template_name="welcome",
            context={"name": "John", "order_id": "456"}
        )

    @pytest.mark.asyncio
    async def test_pagination_parameters(self, mock_template_service):
        """Test that pagination parameters are properly handled."""
        mock_template_list = NotificationTemplateList(
            items=[],
            total=100,
            page=3,
            size=25,
            pages=4
        )
        mock_template_service.list_templates.return_value = mock_template_list
        
        from api.v1.routes import list_templates
        response = await list_templates(3, 25, "email", mock_template_service)
        
        assert response.page == 3
        assert response.size == 25
        mock_template_service.list_templates.assert_called_once_with(3, 25, "email")

    @pytest.mark.asyncio
    async def test_path_parameters(self, mock_log_service):
        """Test that path parameters are properly handled."""
        mock_notification = MagicMock(spec=NotificationLog)
        mock_notification.id = 42
        mock_notification.user_id = 123  # Add the missing user_id attribute
        mock_log_service.get_log.return_value = mock_notification
        
        from api.v1.routes import get_notification_details
        response = await get_notification_details(42, mock_log_service)
        
        assert response.id == 42
        mock_log_service.get_log.assert_called_once_with(42)
