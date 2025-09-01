"""
Mock service implementations for testing.

This module provides mock service classes to avoid circular imports and
provide consistent testing behavior for the service layer.
"""

from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any, Optional, List
import uuid


class MockNotificationService:
    """Mock implementation of NotificationService for testing."""
    
    def __init__(self, db_session):
        self.db = db_session
        self.adapters = {}
        self.template_service = MockNotificationTemplateService(db_session)
        self.log_service = MockNotificationLogService(db_session)
        self.preference_service = MockUserPreferenceService(db_session)
        
        # Load default adapters
        self._load_adapters()
    
    def _load_adapters(self):
        """Load mock adapters for testing."""
        self.adapters = {
            'email': MagicMock(),
            'sms': MagicMock(),
            'push': MagicMock()
        }
        
        # Configure default successful responses
        for adapter in self.adapters.values():
            adapter.send.return_value = {"success": True, "message_id": str(uuid.uuid4())}
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Mock template rendering with simple string formatting."""
        try:
            return template.format(**context)
        except KeyError:
            # Return original template if variables are missing
            return template
    
    async def send_notification(
        self,
        user_id: int,
        template_name: str,
        context: Dict[str, Any],
        notification_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mock notification sending."""
        try:
            # Get template
            template = await self.template_service.get_template_by_name(template_name)
            if not template:
                return {
                    "success": False,
                    "error": f"Template '{template_name}' not found"
                }
            
            # Use template type if not specified
            if not notification_type:
                notification_type = getattr(template, 'type', 'email')
            
            # Check user preferences
            preferences = await self.preference_service.get_user_preference(user_id)
            if preferences and not self._is_notification_enabled(preferences, notification_type):
                return {
                    "success": False,
                    "skipped": True,
                    "error": f"User has disabled {notification_type} notifications"
                }
            
            # Check if adapter exists
            if notification_type not in self.adapters:
                return {
                    "success": False,
                    "error": f"No adapter found for type '{notification_type}'"
                }
            
            # Create log entry
            log_entry = await self.log_service.create_log({
                "user_id": user_id,
                "template_id": getattr(template, 'id', 1),
                "type": notification_type,
                "status": "pending",
                "notification_metadata": context
            })
            
            # Render template
            rendered_subject = self._render_template(getattr(template, 'subject', ''), context)
            rendered_body = self._render_template(getattr(template, 'body', ''), context)
            
            # Send notification
            adapter = self.adapters[notification_type]
            send_result = adapter.send({
                "recipient": context.get("recipient", context.get("user_email", "test@example.com")),
                "subject": rendered_subject,
                "body": rendered_body,
                **context
            })
            
            # Update log with result
            if send_result.get("success"):
                await self.log_service.update_log(getattr(log_entry, 'id', 1), {
                    "status": "sent",
                    "external_id": send_result.get("message_id")
                })
                
                return {
                    "success": True,
                    "notification_id": getattr(log_entry, 'id', 1),
                    "type": notification_type,
                    "template_name": template_name
                }
            else:
                await self.log_service.update_log(getattr(log_entry, 'id', 1), {
                    "status": "failed",
                    "error_message": send_result.get("error", "Unknown error")
                })
                
                return {
                    "success": False,
                    "error": send_result.get("error", "Sending failed")
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _is_notification_enabled(self, preferences, notification_type: str) -> bool:
        """Check if notification type is enabled for user."""
        if notification_type == 'email':
            return getattr(preferences, 'email_enabled', True)
        elif notification_type == 'sms':
            return getattr(preferences, 'sms_enabled', True)
        elif notification_type == 'push':
            return getattr(preferences, 'push_enabled', True)
        return True


class MockNotificationTemplateService:
    """Mock implementation of NotificationTemplateService for testing."""
    
    def __init__(self, db_session):
        self.db = db_session
        self.repository = MagicMock()
        
        # Configure default async methods
        self.repository.create = AsyncMock()
        self.repository.get = AsyncMock()
        self.repository.get_by_name = AsyncMock()
        self.repository.update = AsyncMock()
        self.repository.delete = AsyncMock()
        self.repository.list = AsyncMock()
    
    async def create_template(self, template_data) -> Any:
        """Mock template creation."""
        result = MagicMock()
        result.id = 1
        result.name = getattr(template_data, 'name', 'test_template')
        result.type = getattr(template_data, 'notification_type', 'email')
        result.subject = getattr(template_data, 'subject', 'Test Subject')
        result.body = getattr(template_data, 'body', 'Test Body')
        return result
    
    async def get_template(self, template_id: int) -> Optional[Any]:
        """Mock template retrieval by ID."""
        if template_id <= 0:
            return None
        
        template = MagicMock()
        template.id = template_id
        template.name = f"template_{template_id}"
        template.type = "email"
        template.subject = "Test Subject"
        template.body = "Test Body"
        return template
    
    async def get_template_by_name(self, name: str) -> Optional[Any]:
        """Mock template retrieval by name."""
        if not name or name == "nonexistent_template":
            return None
        
        template = MagicMock()
        template.id = 1
        template.name = name
        template.type = "email"
        template.subject = "Test Subject"
        template.body = "Hello {user_name}, welcome to {app_name}!"
        return template
    
    async def update_template(self, template_id: int, template_update) -> Optional[Any]:
        """Mock template update."""
        if template_id <= 0:
            return None
        
        template = MagicMock()
        template.id = template_id
        template.name = getattr(template_update, 'name', f"updated_template_{template_id}")
        return template
    
    async def delete_template(self, template_id: int) -> bool:
        """Mock template deletion."""
        return template_id > 0
    
    async def list_templates(self, skip: int = 0, limit: int = 100, type_filter: Optional[str] = None) -> Any:
        """Mock template listing."""
        result = MagicMock()
        result.templates = [
            self._create_mock_template(1, "template_1"),
            self._create_mock_template(2, "template_2")
        ]
        result.total = 2
        result.page = 1
        result.per_page = limit
        result.pages = 1
        return result
    
    def _create_mock_template(self, template_id: int, name: str) -> Any:
        """Create a mock template object."""
        template = MagicMock()
        template.id = template_id
        template.name = name
        template.type = "email"
        template.subject = f"Subject for {name}"
        template.body = f"Body for {name}"
        return template


class MockNotificationLogService:
    """Mock implementation of NotificationLogService for testing."""
    
    def __init__(self, db_session):
        self.db = db_session
        self.repository = MagicMock()
        
        # Configure default async methods
        self.repository.create = AsyncMock()
        self.repository.get = AsyncMock()
        self.repository.update = AsyncMock()
        self.repository.list = AsyncMock()
    
    async def create_log(self, log_data) -> Any:
        """Mock log creation."""
        log = MagicMock()
        log.id = 1
        log.user_id = log_data.get('user_id', 123)
        log.template_id = log_data.get('template_id', 1)
        log.type = log_data.get('type', 'email')
        log.status = log_data.get('status', 'pending')
        log.notification_metadata = log_data.get('notification_metadata', {})
        return log
    
    async def get_log(self, log_id: int) -> Optional[Any]:
        """Mock log retrieval by ID."""
        if log_id <= 0:
            return None
        
        log = MagicMock()
        log.id = log_id
        log.user_id = 123
        log.template_id = 1
        log.type = "email"
        log.status = "sent"
        return log
    
    async def update_log(self, log_id: int, log_update) -> Optional[Any]:
        """Mock log update."""
        if log_id <= 0:
            return None
        
        log = MagicMock()
        log.id = log_id
        log.status = log_update.get('status', 'updated')
        log.external_id = log_update.get('external_id')
        log.error_message = log_update.get('error_message')
        return log
    
    async def list_logs(self, skip: int = 0, limit: int = 100, **filters) -> Any:
        """Mock log listing."""
        result = MagicMock()
        result.logs = [
            self._create_mock_log(1, 123),
            self._create_mock_log(2, 456)
        ]
        result.total = 2
        result.page = 1
        result.per_page = limit
        result.pages = 1
        return result
    
    def _create_mock_log(self, log_id: int, user_id: int) -> Any:
        """Create a mock log object."""
        log = MagicMock()
        log.id = log_id
        log.user_id = user_id
        log.template_id = 1
        log.type = "email"
        log.status = "sent"
        return log


class MockUserPreferenceService:
    """Mock implementation of UserPreferenceService for testing."""
    
    def __init__(self, db_session):
        self.db = db_session
        self.repository = MagicMock()
        
        # Configure default async methods
        self.repository.create = AsyncMock()
        self.repository.get_by_user_id = AsyncMock()
        self.repository.update = AsyncMock()
        self.repository.upsert = AsyncMock()
        self.repository.delete = AsyncMock()
        self.repository.list = AsyncMock()
    
    async def create_user_preference(self, preference_data) -> Any:
        """Mock preference creation."""
        preference = MagicMock()
        preference.user_id = preference_data.get('user_id', 123)
        preference.email_enabled = preference_data.get('email_enabled', True)
        preference.sms_enabled = preference_data.get('sms_enabled', True)
        preference.push_enabled = preference_data.get('push_enabled', False)
        return preference
    
    async def get_user_preference(self, user_id: int) -> Optional[Any]:
        """Mock preference retrieval by user ID."""
        if user_id <= 0:
            return None
        
        preference = MagicMock()
        preference.user_id = user_id
        preference.email_enabled = True
        preference.sms_enabled = True
        preference.push_enabled = False
        preference.quiet_hours_start = None
        preference.quiet_hours_end = None
        return preference
    
    async def update_user_preference(self, user_id: int, preference_update) -> Optional[Any]:
        """Mock preference update."""
        if user_id <= 0:
            return None
        
        preference = MagicMock()
        preference.user_id = user_id
        preference.email_enabled = preference_update.get('email_enabled', True)
        preference.sms_enabled = preference_update.get('sms_enabled', True)
        preference.push_enabled = preference_update.get('push_enabled', False)
        return preference
    
    async def upsert_user_preference(self, user_id: int, preference_data) -> Any:
        """Mock preference upsert."""
        preference = MagicMock()
        preference.user_id = user_id
        preference.email_enabled = preference_data.get('email_enabled', True)
        preference.sms_enabled = preference_data.get('sms_enabled', True)
        preference.push_enabled = preference_data.get('push_enabled', False)
        return preference
    
    async def delete_user_preference(self, user_id: int) -> bool:
        """Mock preference deletion."""
        return user_id > 0
    
    async def list_user_preferences(self, skip: int = 0, limit: int = 100) -> Any:
        """Mock preference listing."""
        result = MagicMock()
        result.preferences = [
            self._create_mock_preference(123),
            self._create_mock_preference(456)
        ]
        result.total = 2
        result.page = 1
        result.per_page = limit
        result.pages = 1
        return result
    
    def _create_mock_preference(self, user_id: int) -> Any:
        """Create a mock preference object."""
        preference = MagicMock()
        preference.user_id = user_id
        preference.email_enabled = True
        preference.sms_enabled = True
        preference.push_enabled = False
        preference.quiet_hours_start = None
        preference.quiet_hours_end = None
        return preference
