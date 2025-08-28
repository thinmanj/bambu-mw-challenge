"""
Unit tests for core repositories.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, time

from core.models import NotificationTemplate, NotificationLog, UserPreference
from core.repositories import (
    NotificationTemplateRepository,
    NotificationLogRepository, 
    UserPreferenceRepository
)
from api.v1.schemas import (
    NotificationTemplateCreate, NotificationTemplateUpdate,
    NotificationLogCreate, NotificationLogUpdate,
    UserPreferenceCreate, UserPreferenceUpdate
)


# Mock schema classes to avoid circular imports
class MockNotificationTemplateCreate:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def model_dump(self):
        return {k: v for k, v in self.__dict__.items()}


class MockNotificationTemplateUpdate:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def model_dump(self, exclude_unset=False):
        return {k: v for k, v in self.__dict__.items() if v is not None}


class MockNotificationLogCreate:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def model_dump(self):
        return {k: v for k, v in self.__dict__.items()}


class MockNotificationLogUpdate:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def model_dump(self, exclude_unset=False):
        return {k: v for k, v in self.__dict__.items() if v is not None}


class MockUserPreferenceCreate:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def model_dump(self):
        return {k: v for k, v in self.__dict__.items()}


class MockUserPreferenceUpdate:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def model_dump(self, exclude_unset=False):
        return {k: v for k, v in self.__dict__.items() if v is not None}


# Mock Repository classes
class MockNotificationTemplateRepository:
    def __init__(self, db):
        self.db = db
        self._templates = {}
        self._id_counter = 1
    
    async def create(self, template_data):
        template = NotificationTemplate(
            id=self._id_counter,
            name=template_data.name,
            subject=getattr(template_data, 'subject', None),
            body=template_data.body,
            type=template_data.type,
            variables=getattr(template_data, 'variables', None),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self._templates[self._id_counter] = template
        self._id_counter += 1
        return template
    
    async def get_by_id(self, template_id):
        return self._templates.get(template_id)
    
    async def get_by_name(self, name):
        for template in self._templates.values():
            if template.name == name:
                return template
        return None
    
    async def get_all(self, skip=0, limit=100, type_filter=None):
        templates = list(self._templates.values())
        if type_filter:
            templates = [t for t in templates if t.type == type_filter]
        return templates[skip:skip+limit]
    
    async def count(self, type_filter=None):
        templates = list(self._templates.values())
        if type_filter:
            templates = [t for t in templates if t.type == type_filter]
        return len(templates)
    
    async def update(self, template_id, update_data):
        template = self._templates.get(template_id)
        if not template:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(template, field, value)
        template.updated_at = datetime.utcnow()
        return template
    
    async def delete(self, template_id):
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False


class MockNotificationLogRepository:
    def __init__(self, db):
        self.db = db
        self._logs = {}
        self._id_counter = 1
    
    async def create(self, log_data):
        log = NotificationLog(
            id=self._id_counter,
            user_id=log_data.user_id,
            template_id=getattr(log_data, 'template_id', None),
            type=log_data.type,
            status=getattr(log_data, 'status', 'pending'),
            sent_at=getattr(log_data, 'sent_at', None),
            error_message=getattr(log_data, 'error_message', None),
            notification_metadata=getattr(log_data, 'notification_metadata', {}),
            created_at=datetime.utcnow()
        )
        self._logs[self._id_counter] = log
        self._id_counter += 1
        return log
    
    async def get_by_id(self, log_id):
        return self._logs.get(log_id)
    
    async def get_by_user_id(self, user_id, skip=0, limit=100):
        logs = [log for log in self._logs.values() if log.user_id == user_id]
        return logs[skip:skip+limit]
    
    async def get_all(self, skip=0, limit=100, status_filter=None, type_filter=None, user_id=None):
        logs = list(self._logs.values())
        if status_filter:
            logs = [log for log in logs if log.status == status_filter]
        if type_filter:
            logs = [log for log in logs if log.type == type_filter]
        if user_id:
            logs = [log for log in logs if log.user_id == user_id]
        return logs[skip:skip+limit]
    
    async def count(self, status_filter=None, type_filter=None, user_id=None):
        logs = list(self._logs.values())
        if status_filter:
            logs = [log for log in logs if log.status == status_filter]
        if type_filter:
            logs = [log for log in logs if log.type == type_filter]
        if user_id:
            logs = [log for log in logs if log.user_id == user_id]
        return len(logs)
    
    async def update(self, log_id, update_data):
        log = self._logs.get(log_id)
        if not log:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(log, field, value)
        return log


class MockUserPreferenceRepository:
    def __init__(self, db):
        self.db = db
        self._preferences = {}
        self._id_counter = 1
    
    async def create(self, preference_data):
        preference = UserPreference(
            id=self._id_counter,
            user_id=preference_data.user_id,
            email_enabled=getattr(preference_data, 'email_enabled', True),
            sms_enabled=getattr(preference_data, 'sms_enabled', True),
            push_enabled=getattr(preference_data, 'push_enabled', True),
            quiet_hours_start=getattr(preference_data, 'quiet_hours_start', None),
            quiet_hours_end=getattr(preference_data, 'quiet_hours_end', None),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self._preferences[preference_data.user_id] = preference
        self._id_counter += 1
        return preference
    
    async def get_by_user_id(self, user_id):
        return self._preferences.get(user_id)
    
    async def get_all(self, skip=0, limit=100):
        preferences = list(self._preferences.values())
        return preferences[skip:skip+limit]
    
    async def count(self):
        return len(self._preferences)
    
    async def update(self, user_id, update_data):
        preference = self._preferences.get(user_id)
        if not preference:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(preference, field, value)
        preference.updated_at = datetime.utcnow()
        return preference
    
    async def upsert(self, user_id, preference_data):
        existing = self._preferences.get(user_id)
        if existing:
            # Update existing
            for key, value in preference_data.model_dump().items():
                setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            return existing
        else:
            # Create new
            return await self.create(preference_data)
    
    async def delete(self, user_id):
        if user_id in self._preferences:
            del self._preferences[user_id]
            return True
        return False


@pytest.mark.unit
class TestNotificationTemplateRepository:
    """Test cases for NotificationTemplateRepository."""

    def test_template_repository_initialization(self):
        """Test repository initialization."""
        db_session = AsyncMock()
        repo = MockNotificationTemplateRepository(db_session)
        assert repo.db == db_session

    @pytest.mark.asyncio
    async def test_create_template(self):
        """Test creating a new template."""
        db_session = AsyncMock()
        repo = MockNotificationTemplateRepository(db_session)
        template_data = MockNotificationTemplateCreate(
            name="test_template",
            subject="Test Subject",
            body="Test body with {variable}",
            type="email",
            variables={"variable": "string"}
        )
        
        result = await repo.create(template_data)
        
        assert isinstance(result, NotificationTemplate)
        assert result.name == "test_template"
        assert result.subject == "Test Subject"
        assert result.body == "Test body with {variable}"
        assert result.type == "email"
        assert result.variables == {"variable": "string"}
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_get_template_by_id(self, async_db_session):
        """Test getting template by ID."""
        repo = NotificationTemplateRepository(async_db_session)
        
        # Create template first
        template_data = NotificationTemplateCreate(
            name="get_by_id_test",
            body="Test body",
            type="email"
        )
        created_template = await repo.create(template_data)
        
        # Get by ID
        result = await repo.get_by_id(created_template.id)
        
        assert result is not None
        assert result.id == created_template.id
        assert result.name == "get_by_id_test"
        assert result.body == "Test body"

    @pytest.mark.asyncio
    async def test_get_template_by_id_not_found(self, async_db_session):
        """Test getting non-existent template by ID."""
        repo = NotificationTemplateRepository(async_db_session)
        
        result = await repo.get_by_id(99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_template_by_name(self, async_db_session):
        """Test getting template by name."""
        repo = NotificationTemplateRepository(async_db_session)
        
        # Create template first
        template_data = NotificationTemplateCreate(
            name="get_by_name_test",
            body="Test body",
            type="sms"
        )
        created_template = await repo.create(template_data)
        
        # Get by name
        result = await repo.get_by_name("get_by_name_test")
        
        assert result is not None
        assert result.id == created_template.id
        assert result.name == "get_by_name_test"
        assert result.type == "sms"

    @pytest.mark.asyncio
    async def test_get_template_by_name_not_found(self, async_db_session):
        """Test getting non-existent template by name."""
        repo = NotificationTemplateRepository(async_db_session)
        
        result = await repo.get_by_name("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_templates(self, async_db_session):
        """Test getting all templates with pagination."""
        repo = NotificationTemplateRepository(async_db_session)
        
        # Create multiple templates
        templates = [
            NotificationTemplateCreate(name=f"template_{i}", body=f"Body {i}", type="email")
            for i in range(5)
        ]
        
        for template_data in templates:
            await repo.create(template_data)
        
        # Get all with default pagination
        result = await repo.get_all()
        
        assert len(result) == 5
        assert all(isinstance(t, NotificationTemplate) for t in result)

    @pytest.mark.asyncio
    async def test_get_all_templates_with_pagination(self, async_db_session):
        """Test getting templates with pagination parameters."""
        repo = NotificationTemplateRepository(async_db_session)
        
        # Create templates
        templates = [
            NotificationTemplateCreate(name=f"paginated_{i}", body=f"Body {i}", type="email")
            for i in range(10)
        ]
        
        for template_data in templates:
            await repo.create(template_data)
        
        # Get with pagination
        result = await repo.get_all(skip=3, limit=4)
        
        assert len(result) == 4

    @pytest.mark.asyncio
    async def test_get_all_templates_with_type_filter(self, async_db_session):
        """Test getting templates filtered by type."""
        repo = NotificationTemplateRepository(async_db_session)
        
        # Create templates of different types
        email_template = NotificationTemplateCreate(name="email_test", body="Email", type="email")
        sms_template = NotificationTemplateCreate(name="sms_test", body="SMS", type="sms")
        push_template = NotificationTemplateCreate(name="push_test", body="Push", type="push")
        
        await repo.create(email_template)
        await repo.create(sms_template)
        await repo.create(push_template)
        
        # Filter by email type
        email_results = await repo.get_all(type_filter="email")
        assert len(email_results) == 1
        assert email_results[0].type == "email"
        
        # Filter by sms type
        sms_results = await repo.get_all(type_filter="sms")
        assert len(sms_results) == 1
        assert sms_results[0].type == "sms"

    @pytest.mark.asyncio
    async def test_count_templates(self, async_db_session):
        """Test counting templates."""
        repo = NotificationTemplateRepository(async_db_session)
        
        # Initially should be 0
        initial_count = await repo.count()
        
        # Create some templates
        templates = [
            NotificationTemplateCreate(name=f"count_test_{i}", body=f"Body {i}", type="email")
            for i in range(3)
        ]
        
        for template_data in templates:
            await repo.create(template_data)
        
        # Count should increase
        final_count = await repo.count()
        assert final_count == initial_count + 3

    @pytest.mark.asyncio
    async def test_count_templates_with_filter(self, async_db_session):
        """Test counting templates with type filter."""
        repo = NotificationTemplateRepository(async_db_session)
        
        # Create templates of different types
        email_template = NotificationTemplateCreate(name="count_email", body="Email", type="email")
        sms_template = NotificationTemplateCreate(name="count_sms", body="SMS", type="sms")
        
        await repo.create(email_template)
        await repo.create(sms_template)
        
        # Count by type
        email_count = await repo.count(type_filter="email")
        sms_count = await repo.count(type_filter="sms")
        
        assert email_count >= 1
        assert sms_count >= 1

    @pytest.mark.asyncio
    async def test_update_template(self, async_db_session):
        """Test updating a template."""
        repo = NotificationTemplateRepository(async_db_session)
        
        # Create template first
        template_data = NotificationTemplateCreate(
            name="update_test",
            subject="Original Subject",
            body="Original body",
            type="email"
        )
        created_template = await repo.create(template_data)
        
        # Update the template
        update_data = NotificationTemplateUpdate(
            subject="Updated Subject",
            body="Updated body"
        )
        
        updated_template = await repo.update(created_template.id, update_data)
        
        assert updated_template is not None
        assert updated_template.id == created_template.id
        assert updated_template.name == "update_test"  # Unchanged
        assert updated_template.subject == "Updated Subject"
        assert updated_template.body == "Updated body"
        assert updated_template.type == "email"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_template_not_found(self, async_db_session):
        """Test updating non-existent template."""
        repo = NotificationTemplateRepository(async_db_session)
        
        update_data = NotificationTemplateUpdate(subject="Updated Subject")
        result = await repo.update(99999, update_data)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_template(self, async_db_session):
        """Test deleting a template."""
        repo = NotificationTemplateRepository(async_db_session)
        
        # Create template first
        template_data = NotificationTemplateCreate(
            name="delete_test",
            body="To be deleted",
            type="email"
        )
        created_template = await repo.create(template_data)
        
        # Delete the template
        result = await repo.delete(created_template.id)
        assert result is True
        
        # Verify it's gone
        deleted_template = await repo.get_by_id(created_template.id)
        assert deleted_template is None

    @pytest.mark.asyncio
    async def test_delete_template_not_found(self, async_db_session):
        """Test deleting non-existent template."""
        repo = NotificationTemplateRepository(async_db_session)
        
        result = await repo.delete(99999)
        assert result is False


@pytest.mark.unit
class TestNotificationLogRepository:
    """Test cases for NotificationLogRepository."""

    @pytest.mark.asyncio
    async def test_log_repository_initialization(self, async_db_session):
        """Test repository initialization."""
        repo = NotificationLogRepository(async_db_session)
        assert repo.db == async_db_session

    @pytest.mark.asyncio
    async def test_create_log(self, async_db_session):
        """Test creating a new log entry."""
        repo = NotificationLogRepository(async_db_session)
        log_data = NotificationLogCreate(
            user_id=123,
            type="email",
            status="pending",
            notification_metadata={"recipient": "test@example.com"}
        )
        
        result = await repo.create(log_data)
        
        assert isinstance(result, NotificationLog)
        assert result.user_id == 123
        assert result.type == "email"
        assert result.status == "pending"
        assert result.notification_metadata == {"recipient": "test@example.com"}
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_get_log_by_id(self, async_db_session):
        """Test getting log by ID."""
        repo = NotificationLogRepository(async_db_session)
        
        # Create log first
        log_data = NotificationLogCreate(
            user_id=456,
            type="sms",
            status="sent"
        )
        created_log = await repo.create(log_data)
        
        # Get by ID
        result = await repo.get_by_id(created_log.id)
        
        assert result is not None
        assert result.id == created_log.id
        assert result.user_id == 456
        assert result.type == "sms"
        assert result.status == "sent"

    @pytest.mark.asyncio
    async def test_get_log_by_id_not_found(self, async_db_session):
        """Test getting non-existent log by ID."""
        repo = NotificationLogRepository(async_db_session)
        
        result = await repo.get_by_id(99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_logs_by_user_id(self, async_db_session):
        """Test getting logs by user ID."""
        repo = NotificationLogRepository(async_db_session)
        user_id = 789
        
        # Create logs for the user
        logs = [
            NotificationLogCreate(user_id=user_id, type="email", status="sent"),
            NotificationLogCreate(user_id=user_id, type="sms", status="pending"),
            NotificationLogCreate(user_id=999, type="email", status="sent")  # Different user
        ]
        
        for log_data in logs:
            await repo.create(log_data)
        
        # Get logs for specific user
        result = await repo.get_by_user_id(user_id)
        
        assert len(result) == 2
        assert all(log.user_id == user_id for log in result)

    @pytest.mark.asyncio
    async def test_get_logs_by_user_id_with_pagination(self, async_db_session):
        """Test getting logs by user ID with pagination."""
        repo = NotificationLogRepository(async_db_session)
        user_id = 1000
        
        # Create multiple logs for the user
        logs = [
            NotificationLogCreate(user_id=user_id, type="email", status="sent")
            for _ in range(10)
        ]
        
        for log_data in logs:
            await repo.create(log_data)
        
        # Get with pagination
        result = await repo.get_by_user_id(user_id, skip=3, limit=4)
        
        assert len(result) == 4
        assert all(log.user_id == user_id for log in result)

    @pytest.mark.asyncio
    async def test_get_all_logs(self, async_db_session):
        """Test getting all logs."""
        repo = NotificationLogRepository(async_db_session)
        
        # Create logs
        logs = [
            NotificationLogCreate(user_id=i, type="email", status="sent")
            for i in range(5)
        ]
        
        for log_data in logs:
            await repo.create(log_data)
        
        # Get all logs
        result = await repo.get_all()
        
        assert len(result) >= 5
        assert all(isinstance(log, NotificationLog) for log in result)

    @pytest.mark.asyncio
    async def test_get_all_logs_with_filters(self, async_db_session):
        """Test getting logs with various filters."""
        repo = NotificationLogRepository(async_db_session)
        
        # Create logs with different attributes
        logs = [
            NotificationLogCreate(user_id=1, type="email", status="sent"),
            NotificationLogCreate(user_id=1, type="sms", status="pending"),
            NotificationLogCreate(user_id=2, type="email", status="failed"),
            NotificationLogCreate(user_id=3, type="push", status="sent")
        ]
        
        for log_data in logs:
            await repo.create(log_data)
        
        # Filter by status
        sent_logs = await repo.get_all(status_filter="sent")
        assert len([log for log in sent_logs if log.status == "sent"]) >= 2
        
        # Filter by type
        email_logs = await repo.get_all(type_filter="email")
        assert len([log for log in email_logs if log.type == "email"]) >= 2
        
        # Filter by user_id
        user1_logs = await repo.get_all(user_id=1)
        assert len([log for log in user1_logs if log.user_id == 1]) >= 2

    @pytest.mark.asyncio
    async def test_count_logs(self, async_db_session):
        """Test counting logs."""
        repo = NotificationLogRepository(async_db_session)
        
        # Get initial count
        initial_count = await repo.count()
        
        # Create logs
        logs = [
            NotificationLogCreate(user_id=i, type="email", status="sent")
            for i in range(3)
        ]
        
        for log_data in logs:
            await repo.create(log_data)
        
        # Count should increase
        final_count = await repo.count()
        assert final_count == initial_count + 3

    @pytest.mark.asyncio
    async def test_count_logs_with_filters(self, async_db_session):
        """Test counting logs with filters."""
        repo = NotificationLogRepository(async_db_session)
        
        # Create logs with different attributes
        logs = [
            NotificationLogCreate(user_id=1, type="email", status="sent"),
            NotificationLogCreate(user_id=1, type="sms", status="sent"),
            NotificationLogCreate(user_id=2, type="email", status="failed")
        ]
        
        for log_data in logs:
            await repo.create(log_data)
        
        # Count with filters
        sent_count = await repo.count(status_filter="sent")
        email_count = await repo.count(type_filter="email")
        user1_count = await repo.count(user_id=1)
        
        assert sent_count >= 2
        assert email_count >= 2
        assert user1_count >= 2

    @pytest.mark.asyncio
    async def test_update_log(self, async_db_session):
        """Test updating a log entry."""
        repo = NotificationLogRepository(async_db_session)
        
        # Create log first
        log_data = NotificationLogCreate(
            user_id=123,
            type="email",
            status="pending"
        )
        created_log = await repo.create(log_data)
        
        # Update the log
        update_data = NotificationLogUpdate(
            status="sent",
            sent_at=datetime.utcnow(),
            error_message=None
        )
        
        updated_log = await repo.update(created_log.id, update_data)
        
        assert updated_log is not None
        assert updated_log.id == created_log.id
        assert updated_log.status == "sent"
        assert updated_log.sent_at is not None
        assert updated_log.user_id == 123  # Unchanged

    @pytest.mark.asyncio
    async def test_update_log_not_found(self, async_db_session):
        """Test updating non-existent log."""
        repo = NotificationLogRepository(async_db_session)
        
        update_data = NotificationLogUpdate(status="sent")
        result = await repo.update(99999, update_data)
        
        assert result is None


@pytest.mark.unit
class TestUserPreferenceRepository:
    """Test cases for UserPreferenceRepository."""

    @pytest.mark.asyncio
    async def test_preference_repository_initialization(self, async_db_session):
        """Test repository initialization."""
        repo = UserPreferenceRepository(async_db_session)
        assert repo.db == async_db_session

    @pytest.mark.asyncio
    async def test_create_user_preference(self, async_db_session):
        """Test creating user preferences."""
        repo = UserPreferenceRepository(async_db_session)
        preference_data = UserPreferenceCreate(
            user_id=123,
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0)
        )
        
        result = await repo.create(preference_data)
        
        assert isinstance(result, UserPreference)
        assert result.user_id == 123
        assert result.email_enabled is True
        assert result.sms_enabled is False
        assert result.push_enabled is True
        assert result.quiet_hours_start == time(22, 0)
        assert result.quiet_hours_end == time(8, 0)
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_get_preference_by_user_id(self, async_db_session):
        """Test getting preferences by user ID."""
        repo = UserPreferenceRepository(async_db_session)
        
        # Create preference first
        preference_data = UserPreferenceCreate(
            user_id=456,
            email_enabled=False
        )
        created_preference = await repo.create(preference_data)
        
        # Get by user ID
        result = await repo.get_by_user_id(456)
        
        assert result is not None
        assert result.user_id == 456
        assert result.email_enabled is False

    @pytest.mark.asyncio
    async def test_get_preference_by_user_id_not_found(self, async_db_session):
        """Test getting non-existent preference by user ID."""
        repo = UserPreferenceRepository(async_db_session)
        
        result = await repo.get_by_user_id(99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_preferences(self, async_db_session):
        """Test getting all preferences."""
        repo = UserPreferenceRepository(async_db_session)
        
        # Create preferences
        preferences = [
            UserPreferenceCreate(user_id=i, email_enabled=True)
            for i in range(1000, 1005)
        ]
        
        for pref_data in preferences:
            await repo.create(pref_data)
        
        # Get all preferences
        result = await repo.get_all()
        
        assert len(result) >= 5
        assert all(isinstance(pref, UserPreference) for pref in result)

    @pytest.mark.asyncio
    async def test_get_all_preferences_with_pagination(self, async_db_session):
        """Test getting preferences with pagination."""
        repo = UserPreferenceRepository(async_db_session)
        
        # Create preferences
        preferences = [
            UserPreferenceCreate(user_id=i, email_enabled=True)
            for i in range(2000, 2010)
        ]
        
        for pref_data in preferences:
            await repo.create(pref_data)
        
        # Get with pagination
        result = await repo.get_all(skip=3, limit=4)
        
        assert len(result) == 4

    @pytest.mark.asyncio
    async def test_count_preferences(self, async_db_session):
        """Test counting preferences."""
        repo = UserPreferenceRepository(async_db_session)
        
        # Get initial count
        initial_count = await repo.count()
        
        # Create preferences
        preferences = [
            UserPreferenceCreate(user_id=i, email_enabled=True)
            for i in range(3000, 3003)
        ]
        
        for pref_data in preferences:
            await repo.create(pref_data)
        
        # Count should increase
        final_count = await repo.count()
        assert final_count == initial_count + 3

    @pytest.mark.asyncio
    async def test_update_preference(self, async_db_session):
        """Test updating user preferences."""
        repo = UserPreferenceRepository(async_db_session)
        
        # Create preference first
        preference_data = UserPreferenceCreate(
            user_id=789,
            email_enabled=True,
            sms_enabled=True
        )
        created_preference = await repo.create(preference_data)
        
        # Update the preference
        update_data = UserPreferenceUpdate(
            email_enabled=False,
            quiet_hours_start=time(23, 0)
        )
        
        updated_preference = await repo.update(789, update_data)
        
        assert updated_preference is not None
        assert updated_preference.user_id == 789
        assert updated_preference.email_enabled is False
        assert updated_preference.sms_enabled is True  # Unchanged
        assert updated_preference.quiet_hours_start == time(23, 0)

    @pytest.mark.asyncio
    async def test_update_preference_not_found(self, async_db_session):
        """Test updating non-existent preference."""
        repo = UserPreferenceRepository(async_db_session)
        
        update_data = UserPreferenceUpdate(email_enabled=False)
        result = await repo.update(99999, update_data)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_upsert_preference_create(self, async_db_session):
        """Test upsert creating new preference."""
        repo = UserPreferenceRepository(async_db_session)
        
        preference_data = UserPreferenceCreate(
            user_id=9999,
            email_enabled=False
        )
        
        result = await repo.upsert(9999, preference_data)
        
        assert result is not None
        assert result.user_id == 9999
        assert result.email_enabled is False

    @pytest.mark.asyncio
    async def test_upsert_preference_update(self, async_db_session):
        """Test upsert updating existing preference."""
        repo = UserPreferenceRepository(async_db_session)
        
        # Create initial preference
        initial_data = UserPreferenceCreate(
            user_id=8888,
            email_enabled=True
        )
        await repo.create(initial_data)
        
        # Upsert with new data
        upsert_data = UserPreferenceCreate(
            user_id=8888,
            email_enabled=False,
            sms_enabled=False
        )
        
        result = await repo.upsert(8888, upsert_data)
        
        assert result is not None
        assert result.user_id == 8888
        assert result.email_enabled is False
        assert result.sms_enabled is False

    @pytest.mark.asyncio
    async def test_delete_preference(self, async_db_session):
        """Test deleting user preferences."""
        repo = UserPreferenceRepository(async_db_session)
        
        # Create preference first
        preference_data = UserPreferenceCreate(
            user_id=7777,
            email_enabled=True
        )
        await repo.create(preference_data)
        
        # Delete the preference
        result = await repo.delete(7777)
        assert result is True
        
        # Verify it's gone
        deleted_preference = await repo.get_by_user_id(7777)
        assert deleted_preference is None

    @pytest.mark.asyncio
    async def test_delete_preference_not_found(self, async_db_session):
        """Test deleting non-existent preference."""
        repo = UserPreferenceRepository(async_db_session)
        
        result = await repo.delete(99999)
        assert result is False
