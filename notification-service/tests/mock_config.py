"""
Mock configuration and utilities for testing.

This module provides mock database implementations and utilities to avoid
real database connections during testing.
"""

from unittest.mock import MagicMock
from datetime import datetime, time, timezone
from typing import Dict, List, Any, Optional


class MockDatabase:
    """Mock database for testing purposes."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset the mock database to empty state."""
        self.templates = {}
        self.logs = {}
        self.preferences = {}
        self.next_template_id = 1
        self.next_log_id = 1
    
    # Template operations
    def create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a template record."""
        template = {
            'id': self.next_template_id,
            'name': template_data.get('name'),
            'subject': template_data.get('subject'),
            'body': template_data.get('body'),
            'type': template_data.get('type', 'email'),
            'variables': template_data.get('variables', {}),
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        self.templates[self.next_template_id] = template
        self.next_template_id += 1
        return template
    
    def get_template_by_id(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Get template by ID."""
        return self.templates.get(template_id)
    
    def get_template_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get template by name."""
        for template in self.templates.values():
            if template['name'] == name:
                return template
        return None
    
    def update_template(self, template_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a template."""
        if template_id not in self.templates:
            return None
        
        template = self.templates[template_id].copy()
        template.update(update_data)
        template['updated_at'] = datetime.now(timezone.utc)
        self.templates[template_id] = template
        return template
    
    def delete_template(self, template_id: int) -> bool:
        """Delete a template."""
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False
    
    def list_templates(self, skip: int = 0, limit: int = 100, type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List templates with pagination and filtering."""
        templates = list(self.templates.values())
        
        if type_filter:
            templates = [t for t in templates if t['type'] == type_filter]
        
        return templates[skip:skip + limit]
    
    def count_templates(self, type_filter: Optional[str] = None) -> int:
        """Count templates."""
        templates = list(self.templates.values())
        
        if type_filter:
            templates = [t for t in templates if t['type'] == type_filter]
        
        return len(templates)
    
    # Log operations
    def create_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a log record."""
        log = {
            'id': self.next_log_id,
            'user_id': log_data.get('user_id'),
            'template_id': log_data.get('template_id'),
            'type': log_data.get('type', 'email'),
            'status': log_data.get('status', 'pending'),
            'notification_metadata': log_data.get('notification_metadata', {}),
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        self.logs[self.next_log_id] = log
        self.next_log_id += 1
        return log
    
    def get_log_by_id(self, log_id: int) -> Optional[Dict[str, Any]]:
        """Get log by ID."""
        return self.logs.get(log_id)
    
    def update_log(self, log_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a log."""
        if log_id not in self.logs:
            return None
        
        log = self.logs[log_id].copy()
        log.update(update_data)
        log['updated_at'] = datetime.now(timezone.utc)
        self.logs[log_id] = log
        return log
    
    def list_logs(self, skip: int = 0, limit: int = 100, **filters) -> List[Dict[str, Any]]:
        """List logs with pagination and filtering."""
        logs = list(self.logs.values())
        
        # Apply filters
        for key, value in filters.items():
            if value is not None:
                logs = [l for l in logs if l.get(key) == value]
        
        return logs[skip:skip + limit]
    
    def count_logs(self, **filters) -> int:
        """Count logs."""
        logs = list(self.logs.values())
        
        # Apply filters
        for key, value in filters.items():
            if value is not None:
                logs = [l for l in logs if l.get(key) == value]
        
        return len(logs)
    
    # Preference operations
    def create_preference(self, pref_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a preference record."""
        preference = {
            'user_id': pref_data.get('user_id'),
            'email_enabled': pref_data.get('email_enabled', True),
            'sms_enabled': pref_data.get('sms_enabled', True),
            'push_enabled': pref_data.get('push_enabled', False),
            'quiet_hours_start': pref_data.get('quiet_hours_start'),
            'quiet_hours_end': pref_data.get('quiet_hours_end'),
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        }
        self.preferences[pref_data['user_id']] = preference
        return preference
    
    def get_preference_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get preference by user ID."""
        return self.preferences.get(user_id)
    
    def update_preference(self, user_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a preference."""
        if user_id not in self.preferences:
            return None
        
        preference = self.preferences[user_id].copy()
        preference.update(update_data)
        preference['updated_at'] = datetime.now(timezone.utc)
        self.preferences[user_id] = preference
        return preference
    
    def upsert_preference(self, user_id: int, pref_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert (create or update) a preference."""
        if user_id in self.preferences:
            return self.update_preference(user_id, pref_data)
        else:
            pref_data['user_id'] = user_id
            return self.create_preference(pref_data)
    
    def delete_preference(self, user_id: int) -> bool:
        """Delete a preference."""
        if user_id in self.preferences:
            del self.preferences[user_id]
            return True
        return False
    
    def list_preferences(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List preferences with pagination."""
        preferences = list(self.preferences.values())
        return preferences[skip:skip + limit]
    
    def count_preferences(self) -> int:
        """Count preferences."""
        return len(self.preferences)


# Global mock database instance
mock_db = MockDatabase()


def reset_mock_database():
    """Reset the global mock database."""
    mock_db.reset()


def dict_to_mock_template(template_dict: Dict[str, Any]) -> MagicMock:
    """Convert a template dictionary to a mock template object."""
    mock_template = MagicMock()
    for key, value in template_dict.items():
        setattr(mock_template, key, value)
    return mock_template


def dict_to_mock_log(log_dict: Dict[str, Any]) -> MagicMock:
    """Convert a log dictionary to a mock log object."""
    mock_log = MagicMock()
    for key, value in log_dict.items():
        setattr(mock_log, key, value)
    return mock_log


def dict_to_mock_preference(pref_dict: Dict[str, Any]) -> MagicMock:
    """Convert a preference dictionary to a mock preference object."""
    mock_pref = MagicMock()
    for key, value in pref_dict.items():
        setattr(mock_pref, key, value)
    return mock_pref


class MockSchemas:
    """Mock schema classes for testing."""
    
    def __init__(self):
        # Create mock schema classes
        self.NotificationTemplateCreate = MagicMock()
        self.NotificationTemplateUpdate = MagicMock()
        self.NotificationLogCreate = MagicMock()
        self.NotificationLogUpdate = MagicMock()
        self.UserPreferenceCreate = MagicMock()
        self.UserPreferenceUpdate = MagicMock()


class MockTemplateList:
    """Mock template list response."""
    
    def __init__(self, templates, total, page, per_page, pages):
        self.templates = templates
        self.total = total
        self.page = page
        self.per_page = per_page
        self.pages = pages


class MockLogList:
    """Mock log list response."""
    
    def __init__(self, logs, total, page, per_page, pages):
        self.logs = logs
        self.total = total
        self.page = page
        self.per_page = per_page
        self.pages = pages


class MockPreferenceList:
    """Mock preference list response."""
    
    def __init__(self, preferences, total, page, per_page, pages):
        self.preferences = preferences
        self.total = total
        self.page = page
        self.per_page = per_page
        self.pages = pages
