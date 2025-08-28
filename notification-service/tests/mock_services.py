"""
Mock service implementations to avoid circular imports during testing.
"""
import os
import importlib
from unittest.mock import AsyncMock, MagicMock
import uuid
from datetime import datetime


class MockNotificationService:
    """Mock implementation of the NotificationService."""
    
    def __init__(self, db=None):
        self.db = db
        self.adapters = {}
        self.template_service = MagicMock()
        self.log_service = MagicMock()
        self.preference_service = MagicMock()
        
    def _load_adapters(self):
        """Mock loading adapters."""
        self.adapters = {
            'email': MagicMock(),
            'sms': MagicMock(),
            'push': MagicMock(),
        }
        
    def _render_template(self, template, context):
        """Mock template rendering."""
        if not context:
            return template
            
        try:
            return template.format(**context)
        except KeyError:
            # Return original template if variables are missing
            return template
            
    async def send_notification(self, user_id, template_name, context=None, recipient=None):
        """Mock send notification method."""
        context = context or {}
        
        try:
            # Mock template retrieval
            template = await self.template_service.get_template_by_name(template_name)
            if not template:
                return {
                    "success": False,
                    "error": f"Template '{template_name}' not found",
                    "template_name": template_name
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "template_name": template_name
            }
            
        # Check if notification type is enabled for user
        preferences = await self.preference_service.get_user_preference(user_id, template.notification_type)
        if preferences and not preferences.is_enabled:
            return {
                "success": False,
                "skipped": True,
                "error": f"User has disabled {template.notification_type} notifications",
                "template_name": template_name,
                "type": template.notification_type
            }
            
        # Check if adapter exists
        if template.notification_type not in self.adapters:
            return {
                "success": False,
                "error": f"No adapter found for type '{template.notification_type}'",
                "template_name": template_name,
                "type": template.notification_type
            }
            
        # Mock log creation
        notification_log = MagicMock(id=str(uuid.uuid4()))
        await self.log_service.create_log(
            user_id=user_id,
            notification_type=template.notification_type,
            template_id=template.id,
            recipient=recipient or "",
            subject=template.subject,
            body=template.body,
            context_data=context
        )
        
        # Render template
        rendered_body = self._render_template(template.body, context)
        rendered_subject = None
        if template.subject:
            rendered_subject = self._render_template(template.subject, context)
            
        # Send notification
        adapter = self.adapters[template.notification_type]
        result = adapter.send(
            recipient=recipient,
            subject=rendered_subject,
            body=rendered_body,
            context=context
        )
        
        # Update log with result
        await self.log_service.update_log(
            notification_log.id,
            status="sent" if result.get("success") else "failed",
            external_message_id=result.get("message_id"),
            error_message=result.get("error")
        )
        
        # Return result
        return {
            "success": result.get("success", False),
            "notification_id": notification_log.id,
            "type": template.notification_type,
            "template_name": template_name,
            **({"error": result.get("error")} if not result.get("success") else {})
        }


class MockNotificationTemplateService:
    """Mock implementation of the NotificationTemplateService."""
    
    def __init__(self, db=None):
        self.db = db
        
    async def create_template(self, template_data):
        """Mock create template method."""
        return MagicMock(
            id=1,
            name=template_data.name,
            notification_type=template_data.notification_type,
            subject=template_data.subject,
            body=template_data.body,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
    async def get_template(self, template_id):
        """Mock get template method."""
        return MagicMock(
            id=template_id,
            name=f"template_{template_id}",
            notification_type="email",
            subject="Test Subject",
            body="Test Body",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
    async def get_template_by_name(self, template_name):
        """Mock get template by name method."""
        return MagicMock(
            id=1,
            name=template_name,
            notification_type="email",
            subject="Test Subject",
            body="Test Body with {variable}",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
    async def list_templates(self, skip=0, limit=100, notification_type=None):
        """Mock list templates method."""
        return [
            MagicMock(
                id=i,
                name=f"template_{i}",
                notification_type="email" if i % 3 == 0 else "sms" if i % 3 == 1 else "push",
                subject=f"Test Subject {i}",
                body=f"Test Body {i}",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ) for i in range(1, 6)
        ]
        
    async def update_template(self, template_id, template_data):
        """Mock update template method."""
        return MagicMock(
            id=template_id,
            name=template_data.name,
            notification_type=template_data.notification_type,
            subject=template_data.subject,
            body=template_data.body,
            is_active=template_data.is_active,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
    async def delete_template(self, template_id):
        """Mock delete template method."""
        return True


class MockNotificationLogService:
    """Mock implementation of the NotificationLogService."""
    
    def __init__(self, db=None):
        self.db = db
        
    async def create_log(self, user_id, notification_type, template_id=None, 
                        recipient="", subject=None, body="", context_data=None,
                        status="pending", external_message_id=None, error_message=None):
        """Mock create log method."""
        return MagicMock(
            id=str(uuid.uuid4()),
            user_id=user_id,
            notification_type=notification_type,
            template_id=template_id,
            recipient=recipient,
            subject=subject,
            body=body,
            status=status,
            external_message_id=external_message_id,
            error_message=error_message,
            context_data=context_data or {},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
    async def get_log(self, log_id):
        """Mock get log method."""
        return MagicMock(
            id=log_id,
            user_id="user_123",
            notification_type="email",
            template_id=1,
            recipient="test@example.com",
            subject="Test Subject",
            body="Test Body",
            status="sent",
            external_message_id="msg_123",
            error_message=None,
            context_data={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
    async def get_user_logs(self, user_id, skip=0, limit=100, notification_type=None):
        """Mock get user logs method."""
        return [
            MagicMock(
                id=f"log_{i}",
                user_id=user_id,
                notification_type="email" if i % 3 == 0 else "sms" if i % 3 == 1 else "push",
                template_id=i,
                recipient=f"recipient_{i}",
                subject=f"Subject {i}",
                body=f"Body {i}",
                status="sent" if i % 2 == 0 else "failed",
                external_message_id=f"msg_{i}" if i % 2 == 0 else None,
                error_message=None if i % 2 == 0 else "Error message",
                context_data={},
                created_at=datetime.now(),
                updated_at=datetime.now()
            ) for i in range(1, 6)
        ]
        
    async def update_log(self, log_id, status=None, external_message_id=None, error_message=None):
        """Mock update log method."""
        return MagicMock(
            id=log_id,
            status=status or "sent",
            external_message_id=external_message_id,
            error_message=error_message,
            updated_at=datetime.now()
        )


class MockUserPreferenceService:
    """Mock implementation of the UserPreferenceService."""
    
    def __init__(self, db=None):
        self.db = db
        
    async def get_user_preference(self, user_id, notification_type):
        """Mock get user preference method."""
        return MagicMock(
            id=1,
            user_id=user_id,
            notification_type=notification_type,
            is_enabled=True,
            quiet_hours_start=None,
            quiet_hours_end=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
    async def create_user_preference(self, preference_data):
        """Mock create user preference method."""
        return MagicMock(
            id=1,
            user_id=preference_data.user_id,
            notification_type=preference_data.notification_type,
            is_enabled=preference_data.is_enabled,
            quiet_hours_start=preference_data.quiet_hours_start,
            quiet_hours_end=preference_data.quiet_hours_end,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
    async def update_user_preference(self, preference_id, preference_data):
        """Mock update user preference method."""
        return MagicMock(
            id=preference_id,
            user_id=preference_data.user_id,
            notification_type=preference_data.notification_type,
            is_enabled=preference_data.is_enabled,
            quiet_hours_start=preference_data.quiet_hours_start,
            quiet_hours_end=preference_data.quiet_hours_end,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
    async def upsert_user_preference(self, preference_data):
        """Mock upsert user preference method."""
        return MagicMock(
            id=1,
            user_id=preference_data.user_id,
            notification_type=preference_data.notification_type,
            is_enabled=preference_data.is_enabled,
            quiet_hours_start=preference_data.quiet_hours_start,
            quiet_hours_end=preference_data.quiet_hours_end,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
    async def delete_user_preference(self, preference_id):
        """Mock delete user preference method."""
        return True


# Patch core.services module
import sys
from unittest.mock import MagicMock

# Create a mock module for core.services
mock_core_services = MagicMock()
mock_core_services.NotificationService = MockNotificationService
mock_core_services.NotificationTemplateService = MockNotificationTemplateService
mock_core_services.NotificationLogService = MockNotificationLogService
mock_core_services.UserPreferenceService = MockUserPreferenceService

# Use patch to patch the import system
import sys
from unittest.mock import patch

# Register the mock services with the import system
sys.modules['core.services'] = mock_core_services
