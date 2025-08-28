"""
Shared pytest fixtures and mocks for all tests to avoid circular imports and repetitive mocking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, time
from tests.mock_config import (
    MockDatabase, 
    mock_db,
    reset_mock_database,
    dict_to_mock_template,
    dict_to_mock_log,
    dict_to_mock_preference,
    MockSchemas,
    MockTemplateList,
    MockLogList,
    MockPreferenceList
)

# Reset mock database before each test
@pytest.fixture(autouse=True)
def reset_mock_db():
    """Reset mock database before each test for test isolation."""
    reset_mock_database()
    yield

# Basic database session mock
@pytest.fixture
def mock_db_session():
    """Mock SQLAlchemy database session."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.refresh = AsyncMock()
    return session

# Template fixtures
@pytest.fixture
def sample_template_data():
    """Sample template data for testing."""
    return {
        'name': 'test_template',
        'subject': 'Test Subject',
        'body': 'Hello {name}, this is a test.',
        'type': 'email',
        'variables': {'name': 'string'}
    }

@pytest.fixture 
def mock_notification_template(sample_template_data):
    """Mock NotificationTemplate instance."""
    template_dict = mock_db.create_template(sample_template_data)
    return dict_to_mock_template(template_dict)

# Log fixtures
@pytest.fixture
def sample_log_data():
    """Sample log data for testing."""
    return {
        'user_id': 123,
        'template_id': 1,
        'type': 'email',
        'status': 'pending',
        'notification_metadata': {'recipient': 'test@example.com'}
    }

@pytest.fixture
def mock_notification_log(sample_log_data):
    """Mock NotificationLog instance."""
    log_dict = mock_db.create_log(sample_log_data)
    return dict_to_mock_log(log_dict)

# Preference fixtures
@pytest.fixture
def sample_preference_data():
    """Sample preference data for testing."""
    return {
        'user_id': 123,
        'email_enabled': True,
        'sms_enabled': True,
        'push_enabled': False,
        'quiet_hours_start': time(22, 0),
        'quiet_hours_end': time(8, 0)
    }

@pytest.fixture
def mock_user_preference(sample_preference_data):
    """Mock UserPreference instance."""
    pref_dict = mock_db.create_preference(sample_preference_data)
    return dict_to_mock_preference(pref_dict)

# Repository mocks
@pytest.fixture
def mock_template_repository():
    """Mock NotificationTemplateRepository."""
    repo = MagicMock()
    
    # Create
    async def create_template(template_data):
        data_dict = template_data.model_dump() if hasattr(template_data, 'model_dump') else template_data
        template_dict = mock_db.create_template(data_dict)
        return dict_to_mock_template(template_dict)
    
    # Get by ID
    async def get_template(template_id):
        template_dict = mock_db.get_template_by_id(template_id)
        return dict_to_mock_template(template_dict) if template_dict else None
        
    # Get by name
    async def get_template_by_name(name):
        template_dict = mock_db.get_template_by_name(name)
        return dict_to_mock_template(template_dict) if template_dict else None
    
    # Update
    async def update_template(template_id, template_update):
        data_dict = template_update.model_dump(exclude_unset=True) if hasattr(template_update, 'model_dump') else template_update
        template_dict = mock_db.update_template(template_id, data_dict)
        return dict_to_mock_template(template_dict) if template_dict else None
    
    # Delete
    async def delete_template(template_id):
        return mock_db.delete_template(template_id)
    
    # List
    async def list_templates(skip=0, limit=100, type_filter=None):
        template_dicts = mock_db.list_templates(skip, limit, type_filter)
        templates = [dict_to_mock_template(t) for t in template_dicts]
        total = mock_db.count_templates(type_filter)
        pages = (total + limit - 1) // limit if limit > 0 else 1
        return MockTemplateList(templates, total, skip // limit + 1, limit, pages)
    
    repo.create = AsyncMock(side_effect=create_template)
    repo.get = AsyncMock(side_effect=get_template)
    repo.get_by_name = AsyncMock(side_effect=get_template_by_name)
    repo.update = AsyncMock(side_effect=update_template)
    repo.delete = AsyncMock(side_effect=delete_template)
    repo.list = AsyncMock(side_effect=list_templates)
    
    return repo

@pytest.fixture
def mock_log_repository():
    """Mock NotificationLogRepository."""
    repo = MagicMock()
    
    # Create
    async def create_log(log_data):
        data_dict = log_data.model_dump() if hasattr(log_data, 'model_dump') else log_data
        log_dict = mock_db.create_log(data_dict)
        return dict_to_mock_log(log_dict)
    
    # Get by ID
    async def get_log(log_id):
        log_dict = mock_db.get_log_by_id(log_id)
        return dict_to_mock_log(log_dict) if log_dict else None
    
    # Update
    async def update_log(log_id, log_update):
        data_dict = log_update.model_dump(exclude_unset=True) if hasattr(log_update, 'model_dump') else log_update
        log_dict = mock_db.update_log(log_id, data_dict)
        return dict_to_mock_log(log_dict) if log_dict else None
    
    # List
    async def list_logs(skip=0, limit=100, **filters):
        log_dicts = mock_db.list_logs(skip, limit, **filters)
        logs = [dict_to_mock_log(l) for l in log_dicts]
        total = mock_db.count_logs(**filters)
        pages = (total + limit - 1) // limit if limit > 0 else 1
        return MockLogList(logs, total, skip // limit + 1, limit, pages)
    
    repo.create = AsyncMock(side_effect=create_log)
    repo.get = AsyncMock(side_effect=get_log)
    repo.update = AsyncMock(side_effect=update_log)
    repo.list = AsyncMock(side_effect=list_logs)
    
    return repo

@pytest.fixture
def mock_preference_repository():
    """Mock UserPreferenceRepository."""
    repo = MagicMock()
    
    # Create
    async def create_preference(preference_data):
        data_dict = preference_data.model_dump() if hasattr(preference_data, 'model_dump') else preference_data
        pref_dict = mock_db.create_preference(data_dict)
        return dict_to_mock_preference(pref_dict)
    
    # Get by user ID
    async def get_preference_by_user_id(user_id):
        pref_dict = mock_db.get_preference_by_user_id(user_id)
        return dict_to_mock_preference(pref_dict) if pref_dict else None
    
    # Update
    async def update_preference(user_id, preference_update):
        data_dict = preference_update.model_dump(exclude_unset=True) if hasattr(preference_update, 'model_dump') else preference_update
        pref_dict = mock_db.update_preference(user_id, data_dict)
        return dict_to_mock_preference(pref_dict) if pref_dict else None
    
    # Upsert
    async def upsert_preference(user_id, preference_data):
        data_dict = preference_data.model_dump() if hasattr(preference_data, 'model_dump') else preference_data
        data_dict['user_id'] = user_id
        pref_dict = mock_db.upsert_preference(user_id, data_dict)
        return dict_to_mock_preference(pref_dict)
    
    # Delete
    async def delete_preference(user_id):
        return mock_db.delete_preference(user_id)
    
    # List
    async def list_preferences(skip=0, limit=100):
        pref_dicts = mock_db.list_preferences(skip, limit)
        preferences = [dict_to_mock_preference(p) for p in pref_dicts]
        total = mock_db.count_preferences()
        pages = (total + limit - 1) // limit if limit > 0 else 1
        return MockPreferenceList(preferences, total, skip // limit + 1, limit, pages)
    
    repo.create = AsyncMock(side_effect=create_preference)
    repo.get_by_user_id = AsyncMock(side_effect=get_preference_by_user_id)
    repo.update = AsyncMock(side_effect=update_preference)
    repo.upsert = AsyncMock(side_effect=upsert_preference)
    repo.delete = AsyncMock(side_effect=delete_preference)
    repo.list = AsyncMock(side_effect=list_preferences)
    
    return repo

# Service mocks that use the repositories
@pytest.fixture
def mock_template_service(mock_template_repository):
    """Mock NotificationTemplateService with repository."""
    service = MagicMock()
    service.repository = mock_template_repository
    
    # Delegate methods to repository
    service.create_template = mock_template_repository.create
    service.get_template = mock_template_repository.get
    service.get_template_by_name = mock_template_repository.get_by_name
    service.update_template = mock_template_repository.update
    service.delete_template = mock_template_repository.delete
    service.list_templates = mock_template_repository.list
    
    return service

@pytest.fixture
def mock_log_service(mock_log_repository):
    """Mock NotificationLogService with repository."""
    service = MagicMock()
    service.repository = mock_log_repository
    
    # Delegate methods to repository
    service.create_log = mock_log_repository.create
    service.get_log = mock_log_repository.get
    service.update_log = mock_log_repository.update
    service.list_logs = mock_log_repository.list
    
    return service

@pytest.fixture
def mock_preference_service(mock_preference_repository):
    """Mock UserPreferenceService with repository."""
    service = MagicMock()
    service.repository = mock_preference_repository
    
    # Delegate methods to repository  
    service.create_user_preference = mock_preference_repository.create
    service.get_user_preference = mock_preference_repository.get_by_user_id
    service.update_user_preference = mock_preference_repository.update
    service.upsert_user_preference = mock_preference_repository.upsert
    service.delete_user_preference = mock_preference_repository.delete
    service.list_user_preferences = mock_preference_repository.list
    
    return service

# Mock schemas for testing
@pytest.fixture
def mock_schemas():
    """Mock schema classes."""
    return MockSchemas()
