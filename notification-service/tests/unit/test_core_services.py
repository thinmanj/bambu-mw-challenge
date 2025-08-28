"""
Unit tests for core services.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, time
import uuid
import os
import logging

# Avoid circular import by importing locally in tests
from core.models import NotificationTemplate, NotificationLog, UserPreference, NotificationStatus
from api.v1.schemas import (
    NotificationTemplateCreate, NotificationTemplateUpdate,
    NotificationLogCreate, NotificationLogUpdate,
    UserPreferenceCreate, UserPreferenceUpdate,
    NotificationTemplateList, NotificationLogList, UserPreferenceList
)


@pytest.mark.unit
class TestNotificationTemplateService:
    """Test cases for NotificationTemplateService."""

    def test_service_initialization(self):
        """Test service initialization."""
        from core.services import NotificationTemplateService
        mock_db = MagicMock()
        service = NotificationTemplateService(mock_db)
        assert service.repository is not None
        assert service.repository.db == mock_db

    @pytest.mark.asyncio
    async def test_create_template(self):
        """Test creating a template."""
        from core.services import NotificationTemplateService
        mock_db = MagicMock()
        service = NotificationTemplateService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        mock_template = MagicMock(spec=NotificationTemplate)
        service.repository.create.return_value = mock_template
        
        template_data = NotificationTemplateCreate(
            name="test_template",
            body="Test body",
            type="email"
        )
        
        result = await service.create_template(template_data)
        
        assert result == mock_template
        service.repository.create.assert_called_once_with(template_data)

    @pytest.mark.asyncio
    async def test_get_template(self):
        """Test getting template by ID."""
        mock_db = MagicMock()
        service = NotificationTemplateService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        mock_template = MagicMock(spec=NotificationTemplate)
        service.repository.get_by_id.return_value = mock_template
        
        result = await service.get_template(1)
        
        assert result == mock_template
        service.repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_template_by_name(self):
        """Test getting template by name."""
        mock_db = MagicMock()
        service = NotificationTemplateService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        mock_template = MagicMock(spec=NotificationTemplate)
        service.repository.get_by_name.return_value = mock_template
        
        result = await service.get_template_by_name("test_template")
        
        assert result == mock_template
        service.repository.get_by_name.assert_called_once_with("test_template")

    @pytest.mark.asyncio
    async def test_list_templates(self):
        """Test listing templates with pagination."""
        mock_db = MagicMock()
        service = NotificationTemplateService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        mock_templates = [MagicMock(spec=NotificationTemplate) for _ in range(3)]
        service.repository.get_all.return_value = mock_templates
        service.repository.count.return_value = 10
        
        result = await service.list_templates(page=2, size=3, type_filter="email")
        
        assert isinstance(result, NotificationTemplateList)
        assert result.items == mock_templates
        assert result.total == 10
        assert result.page == 2
        assert result.size == 3
        assert result.pages == 4  # ceil(10/3) = 4
        
        service.repository.get_all.assert_called_once_with(3, 3, "email")  # skip = (2-1)*3 = 3
        service.repository.count.assert_called_once_with("email")

    @pytest.mark.asyncio
    async def test_list_templates_empty(self):
        """Test listing templates with no results."""
        mock_db = MagicMock()
        service = NotificationTemplateService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        service.repository.get_all.return_value = []
        service.repository.count.return_value = 0
        
        result = await service.list_templates()
        
        assert isinstance(result, NotificationTemplateList)
        assert result.items == []
        assert result.total == 0
        assert result.page == 1
        assert result.size == 50
        assert result.pages == 1

    @pytest.mark.asyncio
    async def test_update_template(self):
        """Test updating a template."""
        mock_db = MagicMock()
        service = NotificationTemplateService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        mock_template = MagicMock(spec=NotificationTemplate)
        service.repository.update.return_value = mock_template
        
        update_data = NotificationTemplateUpdate(subject="Updated Subject")
        
        result = await service.update_template(1, update_data)
        
        assert result == mock_template
        service.repository.update.assert_called_once_with(1, update_data)

    @pytest.mark.asyncio
    async def test_delete_template(self):
        """Test deleting a template."""
        mock_db = MagicMock()
        service = NotificationTemplateService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        service.repository.delete.return_value = True
        
        result = await service.delete_template(1)
        
        assert result is True
        service.repository.delete.assert_called_once_with(1)


@pytest.mark.unit
class TestNotificationLogService:
    """Test cases for NotificationLogService."""

    def test_service_initialization(self):
        """Test service initialization."""
        from core.services import NotificationLogService
        mock_db = MagicMock()
        service = NotificationLogService(mock_db)
        assert service.repository is not None
        assert service.repository.db == mock_db

    @pytest.mark.asyncio
    async def test_create_log(self):
        """Test creating a log entry."""
        mock_db = MagicMock()
        service = NotificationLogService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        mock_log = MagicMock(spec=NotificationLog)
        service.repository.create.return_value = mock_log
        
        log_data = NotificationLogCreate(
            user_id=123,
            type="email",
            status="pending"
        )
        
        result = await service.create_log(log_data)
        
        assert result == mock_log
        service.repository.create.assert_called_once_with(log_data)

    @pytest.mark.asyncio
    async def test_get_log(self):
        """Test getting log by ID."""
        mock_db = MagicMock()
        service = NotificationLogService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        mock_log = MagicMock(spec=NotificationLog)
        service.repository.get_by_id.return_value = mock_log
        
        result = await service.get_log(1)
        
        assert result == mock_log
        service.repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_user_logs(self):
        """Test getting logs for a user."""
        mock_db = MagicMock()
        service = NotificationLogService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        mock_logs = [MagicMock(spec=NotificationLog) for _ in range(2)]
        service.repository.get_by_user_id.return_value = mock_logs
        service.repository.count.return_value = 5
        
        result = await service.get_user_logs(123, page=1, size=2)
        
        assert isinstance(result, NotificationLogList)
        assert result.items == mock_logs
        assert result.total == 5
        assert result.page == 1
        assert result.size == 2
        assert result.pages == 3  # ceil(5/2) = 3
        
        service.repository.get_by_user_id.assert_called_once_with(123, 0, 2)
        service.repository.count.assert_called_once_with(user_id=123)

    @pytest.mark.asyncio
    async def test_list_logs(self):
        """Test listing logs with filters."""
        mock_db = MagicMock()
        service = NotificationLogService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        mock_logs = [MagicMock(spec=NotificationLog) for _ in range(3)]
        service.repository.get_all.return_value = mock_logs
        service.repository.count.return_value = 8
        
        result = await service.list_logs(
            page=2, size=3, 
            status_filter="sent", 
            type_filter="email", 
            user_id=456
        )
        
        assert isinstance(result, NotificationLogList)
        assert result.items == mock_logs
        assert result.total == 8
        assert result.page == 2
        assert result.size == 3
        assert result.pages == 3  # ceil(8/3) = 3
        
        service.repository.get_all.assert_called_once_with(3, 3, "sent", "email", 456)
        service.repository.count.assert_called_once_with("sent", "email", 456)

    @pytest.mark.asyncio
    async def test_update_log(self):
        """Test updating a log entry."""
        mock_db = MagicMock()
        service = NotificationLogService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        mock_log = MagicMock(spec=NotificationLog)
        service.repository.update.return_value = mock_log
        
        update_data = NotificationLogUpdate(status="sent")
        
        result = await service.update_log(1, update_data)
        
        assert result == mock_log
        service.repository.update.assert_called_once_with(1, update_data)


@pytest.mark.unit
class TestUserPreferenceService:
    """Test cases for UserPreferenceService."""

    def test_service_initialization(self):
        """Test service initialization."""
        mock_db = MagicMock()
        service = UserPreferenceService(mock_db)
        assert service.repository is not None
        assert service.repository.db == mock_db

    @pytest.mark.asyncio
    async def test_get_user_preference(self):
        """Test getting user preferences."""
        mock_db = MagicMock()
        service = UserPreferenceService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        mock_preference = MagicMock(spec=UserPreference)
        service.repository.get_by_user_id.return_value = mock_preference
        
        result = await service.get_user_preference(123)
        
        assert result == mock_preference
        service.repository.get_by_user_id.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_create_user_preference(self):
        """Test creating user preferences."""
        mock_db = MagicMock()
        service = UserPreferenceService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        mock_preference = MagicMock(spec=UserPreference)
        service.repository.create.return_value = mock_preference
        
        preference_data = UserPreferenceCreate(user_id=123, email_enabled=False)
        
        result = await service.create_user_preference(preference_data)
        
        assert result == mock_preference
        service.repository.create.assert_called_once_with(preference_data)

    @pytest.mark.asyncio
    async def test_update_user_preference(self):
        """Test updating user preferences."""
        mock_db = MagicMock()
        service = UserPreferenceService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        mock_preference = MagicMock(spec=UserPreference)
        service.repository.update.return_value = mock_preference
        
        preference_data = UserPreferenceUpdate(email_enabled=False)
        
        result = await service.update_user_preference(123, preference_data)
        
        assert result == mock_preference
        service.repository.update.assert_called_once_with(123, preference_data)

    @pytest.mark.asyncio
    async def test_upsert_user_preference(self):
        """Test upserting user preferences."""
        mock_db = MagicMock()
        service = UserPreferenceService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        mock_preference = MagicMock(spec=UserPreference)
        service.repository.upsert.return_value = mock_preference
        
        preference_data = UserPreferenceCreate(user_id=123, email_enabled=False)
        
        result = await service.upsert_user_preference(123, preference_data)
        
        assert result == mock_preference
        service.repository.upsert.assert_called_once_with(123, preference_data)

    @pytest.mark.asyncio
    async def test_delete_user_preference(self):
        """Test deleting user preferences."""
        mock_db = MagicMock()
        service = UserPreferenceService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        service.repository.delete.return_value = True
        
        result = await service.delete_user_preference(123)
        
        assert result is True
        service.repository.delete.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_list_preferences(self):
        """Test listing user preferences."""
        mock_db = MagicMock()
        service = UserPreferenceService(mock_db)
        
        # Mock repository
        service.repository = AsyncMock()
        mock_preferences = [MagicMock(spec=UserPreference) for _ in range(2)]
        service.repository.get_all.return_value = mock_preferences
        service.repository.count.return_value = 7
        
        result = await service.list_preferences(page=2, size=2)
        
        assert isinstance(result, UserPreferenceList)
        assert result.items == mock_preferences
        assert result.total == 7
        assert result.page == 2
        assert result.size == 2
        assert result.pages == 4  # ceil(7/2) = 4
        
        service.repository.get_all.assert_called_once_with(2, 2)  # skip = (2-1)*2 = 2
        service.repository.count.assert_called_once()


@pytest.mark.unit
class TestNotificationService:
    """Test cases for NotificationService."""

    @patch('core.services.NotificationTemplateService')
    @patch('core.services.NotificationLogService')
    @patch('core.services.UserPreferenceService')
    def test_service_initialization(self, mock_user_pref_service, mock_log_service, mock_template_service):
        """Test service initialization."""
        mock_db = MagicMock()
        
        service = NotificationService(mock_db)
        
        assert service.db == mock_db
        assert service.template_service is not None
        assert service.log_service is not None
        assert service.preference_service is not None
        assert service.adapters == {}

    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('importlib.import_module')
    def test_load_adapters_success(self, mock_import, mock_listdir, mock_exists):
        """Test successful adapter loading."""
        mock_db = MagicMock()
        mock_exists.return_value = True
        mock_listdir.return_value = ['email.py', 'sms.py', '__init__.py', 'push.py']
        
        # Mock modules and provider classes
        mock_email_module = MagicMock()
        mock_email_provider = MagicMock()
        mock_email_provider.__name__ = 'EmailProvider'
        mock_email_module.EmailProvider = mock_email_provider
        mock_email_module.__dict__ = {'EmailProvider': mock_email_provider}
        
        mock_sms_module = MagicMock()
        mock_sms_provider = MagicMock()
        mock_sms_provider.__name__ = 'SMSProvider'
        mock_sms_module.SMSProvider = mock_sms_provider
        mock_sms_module.__dict__ = {'SMSProvider': mock_sms_provider}
        
        mock_push_module = MagicMock()
        mock_push_provider = MagicMock()
        mock_push_provider.__name__ = 'PushProvider'
        mock_push_module.PushProvider = mock_push_provider
        mock_push_module.__dict__ = {'PushProvider': mock_push_provider}
        
        def mock_import_side_effect(module_name):
            if module_name == 'adapters.email':
                return mock_email_module
            elif module_name == 'adapters.sms':
                return mock_sms_module
            elif module_name == 'adapters.push':
                return mock_push_module
            raise ImportError(f"No module named '{module_name}'")
        
        mock_import.side_effect = mock_import_side_effect
        
        # Create service and test adapter loading
        service = NotificationService(mock_db)
        
        # Verify adapters were loaded
        assert len(service.adapters) == 3
        assert 'email' in service.adapters
        assert 'sms' in service.adapters
        assert 'push' in service.adapters

    @patch('os.path.exists')
    def test_load_adapters_no_directory(self, mock_exists):
        """Test adapter loading when adapters directory doesn't exist."""
        mock_db = MagicMock()
        mock_exists.return_value = False
        
        with patch('logging.getLogger') as mock_logger:
            mock_log = MagicMock()
            mock_logger.return_value = mock_log
            
            service = NotificationService(mock_db)
            
            # Should log warning and have no adapters
            assert len(service.adapters) == 0
            mock_log.warning.assert_called()

    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('importlib.import_module')
    def test_load_adapters_import_error(self, mock_import, mock_listdir, mock_exists):
        """Test adapter loading with import errors."""
        mock_db = MagicMock()
        mock_exists.return_value = True
        mock_listdir.return_value = ['broken.py']
        mock_import.side_effect = ImportError("Module not found")
        
        with patch('logging.getLogger') as mock_logger:
            mock_log = MagicMock()
            mock_logger.return_value = mock_log
            
            service = NotificationService(mock_db)
            
            # Should log error and have no adapters
            assert len(service.adapters) == 0
            mock_log.error.assert_called()

    def test_render_template_success(self):
        """Test successful template rendering."""
        mock_db = MagicMock()
        service = NotificationService(mock_db)
        
        template = "Hello {name}, your order {order_id} is ready!"
        context = {"name": "John", "order_id": "12345"}
        
        result = service._render_template(template, context)
        
        assert result == "Hello John, your order 12345 is ready!"

    def test_render_template_missing_variable(self):
        """Test template rendering with missing variable."""
        mock_db = MagicMock()
        service = NotificationService(mock_db)
        
        template = "Hello {name}, your order {order_id} is ready!"
        context = {"name": "John"}  # Missing order_id
        
        with patch('logging.getLogger') as mock_logger:
            mock_log = MagicMock()
            mock_logger.return_value = mock_log
            
            result = service._render_template(template, context)
            
            # Should return original template and log warning
            assert result == template
            mock_log.warning.assert_called()

    @pytest.mark.asyncio
    async def test_send_notification_template_not_found(self):
        """Test sending notification with non-existent template."""
        mock_db = MagicMock()
        service = NotificationService(mock_db)
        
        # Mock services
        service.template_service = AsyncMock()
        service.template_service.get_template_by_name.return_value = None
        
        result = await service.send_notification(
            user_id=123,
            template_name="nonexistent",
            context={}
        )
        
        assert result["success"] is False
        assert "Template 'nonexistent' not found" in result["error"]
        assert "notification_id" in result

    @pytest.mark.asyncio
    async def test_send_notification_user_preferences_disabled(self):
        """Test sending notification with user preferences disabled."""
        mock_db = MagicMock()
        service = NotificationService(mock_db)
        
        # Mock template
        mock_template = MagicMock()
        mock_template.type = "email"
        mock_template.subject = "Test Subject"
        mock_template.body = "Test Body"
        
        # Mock user preferences (email disabled)
        mock_preferences = MagicMock()
        mock_preferences.email_enabled = False
        
        # Mock services
        service.template_service = AsyncMock()
        service.template_service.get_template_by_name.return_value = mock_template
        service.preference_service = AsyncMock()
        service.preference_service.get_user_preference.return_value = mock_preferences
        
        result = await service.send_notification(
            user_id=123,
            template_name="test_template",
            context={}
        )
        
        assert result["success"] is False
        assert result["skipped"] is True
        assert "User has disabled email notifications" in result["error"]

    @pytest.mark.asyncio
    async def test_send_notification_no_adapter(self):
        """Test sending notification with no adapter for type."""
        mock_db = MagicMock()
        service = NotificationService(mock_db)
        service.adapters = {}  # No adapters
        
        # Mock template
        mock_template = MagicMock()
        mock_template.type = "email"
        mock_template.subject = "Test Subject"
        mock_template.body = "Test Body"
        
        # Mock services
        service.template_service = AsyncMock()
        service.template_service.get_template_by_name.return_value = mock_template
        service.preference_service = AsyncMock()
        service.preference_service.get_user_preference.return_value = None
        
        result = await service.send_notification(
            user_id=123,
            template_name="test_template",
            context={}
        )
        
        assert result["success"] is False
        assert "No adapter found for type 'email'" in result["error"]

    @pytest.mark.asyncio
    async def test_send_notification_success(self):
        """Test successful notification sending."""
        mock_db = MagicMock()
        service = NotificationService(mock_db)
        
        # Mock template
        mock_template = MagicMock()
        mock_template.type = "email"
        mock_template.subject = "Hello {name}"
        mock_template.body = "Welcome {name} to our service!"
        
        # Mock adapter
        mock_adapter = MagicMock()
        mock_adapter.send.return_value = {"success": True, "message_id": "msg_123"}
        service.adapters = {"email": mock_adapter}
        
        # Mock log
        mock_log = MagicMock()
        mock_log.id = "log_123"
        
        # Mock services
        service.template_service = AsyncMock()
        service.template_service.get_template_by_name.return_value = mock_template
        service.preference_service = AsyncMock()
        service.preference_service.get_user_preference.return_value = None
        service.log_service = AsyncMock()
        service.log_service.create_log.return_value = mock_log
        service.log_service.update_log.return_value = None
        
        result = await service.send_notification(
            user_id=123,
            template_name="test_template",
            context={"name": "John"}
        )
        
        assert result["success"] is True
        assert result["type"] == "email"
        assert result["template_name"] == "test_template"
        assert "notification_id" in result
        
        # Verify adapter was called with rendered content
        mock_adapter.send.assert_called_once()
        call_args = mock_adapter.send.call_args[0][0]
        assert "subject" in call_args
        assert "body" in call_args
        assert call_args["subject"] == "Hello John"
        assert call_args["body"] == "Welcome John to our service!"

    @pytest.mark.asyncio
    async def test_send_notification_adapter_failure(self):
        """Test notification sending with adapter failure."""
        mock_db = MagicMock()
        service = NotificationService(mock_db)
        
        # Mock template
        mock_template = MagicMock()
        mock_template.type = "email"
        mock_template.subject = "Test Subject"
        mock_template.body = "Test Body"
        
        # Mock adapter that fails
        mock_adapter = MagicMock()
        mock_adapter.send.return_value = {"success": False, "error": "SMTP error"}
        service.adapters = {"email": mock_adapter}
        
        # Mock log
        mock_log = MagicMock()
        mock_log.id = "log_123"
        
        # Mock services
        service.template_service = AsyncMock()
        service.template_service.get_template_by_name.return_value = mock_template
        service.preference_service = AsyncMock()
        service.preference_service.get_user_preference.return_value = None
        service.log_service = AsyncMock()
        service.log_service.create_log.return_value = mock_log
        service.log_service.update_log.return_value = None
        
        result = await service.send_notification(
            user_id=123,
            template_name="test_template",
            context={}
        )
        
        assert result["success"] is False
        assert result["error"] == "SMTP error"
        
        # Verify log was updated with failure status
        service.log_service.update_log.assert_called()
        update_call_args = service.log_service.update_log.call_args[0][1]
        assert update_call_args.status == NotificationStatus.FAILED
        assert update_call_args.error_message == "SMTP error"

    @pytest.mark.asyncio
    async def test_send_notification_exception_handling(self):
        """Test notification sending with exception."""
        mock_db = MagicMock()
        service = NotificationService(mock_db)
        
        # Mock services that raise exception
        service.template_service = AsyncMock()
        service.template_service.get_template_by_name.side_effect = Exception("Database error")
        
        result = await service.send_notification(
            user_id=123,
            template_name="test_template",
            context={}
        )
        
        assert result["success"] is False
        assert "Database error" in result["error"]
        assert "notification_id" in result

    @pytest.mark.asyncio
    async def test_send_notification_with_user_preferences_enabled(self):
        """Test sending notification with user preferences enabled."""
        mock_db = MagicMock()
        service = NotificationService(mock_db)
        
        # Mock template
        mock_template = MagicMock()
        mock_template.type = "email"
        mock_template.subject = "Test Subject"
        mock_template.body = "Test Body"
        
        # Mock user preferences (email enabled)
        mock_preferences = MagicMock()
        mock_preferences.email_enabled = True
        
        # Mock adapter
        mock_adapter = MagicMock()
        mock_adapter.send.return_value = {"success": True, "message_id": "msg_123"}
        service.adapters = {"email": mock_adapter}
        
        # Mock log
        mock_log = MagicMock()
        mock_log.id = "log_123"
        
        # Mock services
        service.template_service = AsyncMock()
        service.template_service.get_template_by_name.return_value = mock_template
        service.preference_service = AsyncMock()
        service.preference_service.get_user_preference.return_value = mock_preferences
        service.log_service = AsyncMock()
        service.log_service.create_log.return_value = mock_log
        service.log_service.update_log.return_value = None
        
        result = await service.send_notification(
            user_id=123,
            template_name="test_template",
            context={}
        )
        
        assert result["success"] is True
        assert result["type"] == "email"
        
        # Verify log was updated with success status
        service.log_service.update_log.assert_called()
        update_call_args = service.log_service.update_log.call_args[0][1]
        assert update_call_args.status == NotificationStatus.SENT
