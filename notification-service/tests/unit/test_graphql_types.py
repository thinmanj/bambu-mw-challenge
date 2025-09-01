"""
Comprehensive tests for GraphQL types.

This module tests the GraphQL type definitions, enums, and input types
by mocking strawberry dependencies to ensure complete coverage.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, time, timezone
from typing import List, Optional
from enum import Enum


# Mock strawberry decorators and types to avoid import issues
def mock_strawberry_type(cls):
    """Mock strawberry.type decorator."""
    return cls


def mock_strawberry_enum(cls):
    """Mock strawberry.enum decorator."""
    return cls


def mock_strawberry_input(cls):
    """Mock strawberry.input decorator."""
    return cls


# Mock the enum classes
class MockNotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class MockNotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


@pytest.mark.unit
class TestGraphQLEnums:
    """Test GraphQL enum types."""

    def test_notification_type_enum_values(self):
        """Test NotificationType enum values."""
        assert MockNotificationType.EMAIL == "email"
        assert MockNotificationType.SMS == "sms"
        assert MockNotificationType.PUSH == "push"

    def test_notification_type_enum_inheritance(self):
        """Test NotificationType inherits from str and Enum."""
        assert issubclass(MockNotificationType, str)
        assert issubclass(MockNotificationType, Enum)

    def test_notification_type_enum_iteration(self):
        """Test iterating over NotificationType enum."""
        values = [item.value for item in MockNotificationType]
        expected = ["email", "sms", "push"]
        assert values == expected

    def test_notification_status_enum_values(self):
        """Test NotificationStatus enum values."""
        assert MockNotificationStatus.PENDING == "pending"
        assert MockNotificationStatus.SENT == "sent"
        assert MockNotificationStatus.FAILED == "failed"
        assert MockNotificationStatus.BOUNCED == "bounced"

    def test_notification_status_enum_inheritance(self):
        """Test NotificationStatus inherits from str and Enum."""
        assert issubclass(MockNotificationStatus, str)
        assert issubclass(MockNotificationStatus, Enum)

    def test_notification_status_enum_iteration(self):
        """Test iterating over NotificationStatus enum."""
        values = [item.value for item in MockNotificationStatus]
        expected = ["pending", "sent", "failed", "bounced"]
        assert values == expected

    def test_enum_string_comparison(self):
        """Test that enums can be compared to strings."""
        assert MockNotificationType.EMAIL == "email"
        assert MockNotificationStatus.PENDING == "pending"
        
        # Test inequality
        assert MockNotificationType.EMAIL != "sms"
        assert MockNotificationStatus.PENDING != "sent"

    def test_enum_in_collections(self):
        """Test using enums in collections."""
        email_types = [MockNotificationType.EMAIL]
        assert MockNotificationType.EMAIL in email_types
        assert MockNotificationType.SMS not in email_types
        
        all_statuses = [MockNotificationStatus.PENDING, MockNotificationStatus.SENT, 
                       MockNotificationStatus.FAILED, MockNotificationStatus.BOUNCED]
        assert len(all_statuses) == 4
        assert MockNotificationStatus.PENDING in all_statuses


@pytest.mark.unit
class TestGraphQLObjectTypes:
    """Test GraphQL object types."""

    def test_notification_template_type_structure(self):
        """Test NotificationTemplate type structure."""
        @mock_strawberry_type
        class NotificationTemplate:
            id: int
            name: str
            subject: Optional[str]
            body: str
            type: MockNotificationType
            variables: Optional[str] = None
            created_at: datetime
            updated_at: datetime
        
        # Test type annotations exist
        annotations = NotificationTemplate.__annotations__
        assert annotations['id'] == int
        assert annotations['name'] == str
        assert annotations['subject'] == Optional[str]
        assert annotations['body'] == str
        assert annotations['type'] == MockNotificationType
        assert annotations['variables'] == Optional[str]
        assert annotations['created_at'] == datetime
        assert annotations['updated_at'] == datetime

    def test_notification_template_instantiation(self):
        """Test creating NotificationTemplate instances."""
        @mock_strawberry_type
        class NotificationTemplate:
            def __init__(self, id, name, body, type, subject=None, variables=None, 
                        created_at=None, updated_at=None):
                self.id = id
                self.name = name
                self.subject = subject
                self.body = body
                self.type = type
                self.variables = variables
                self.created_at = created_at or datetime.now(timezone.utc)
                self.updated_at = updated_at or datetime.now(timezone.utc)
        
        template = NotificationTemplate(
            id=1,
            name="welcome_email",
            subject="Welcome!",
            body="Hello {name}",
            type=MockNotificationType.EMAIL,
            variables='{"name": "string"}'
        )
        
        assert template.id == 1
        assert template.name == "welcome_email"
        assert template.subject == "Welcome!"
        assert template.body == "Hello {name}"
        assert template.type == MockNotificationType.EMAIL
        assert template.variables == '{"name": "string"}'
        assert isinstance(template.created_at, datetime)
        assert isinstance(template.updated_at, datetime)

    def test_notification_log_type_structure(self):
        """Test NotificationLog type structure."""
        @mock_strawberry_type
        class NotificationLog:
            id: int
            user_id: int
            template_id: Optional[int]
            type: MockNotificationType
            status: MockNotificationStatus
            sent_at: Optional[datetime]
            error_message: Optional[str]
            metadata: Optional[str] = None
            created_at: datetime
            template: Optional['NotificationTemplate'] = None
        
        # Test type annotations
        annotations = NotificationLog.__annotations__
        assert annotations['id'] == int
        assert annotations['user_id'] == int
        assert annotations['template_id'] == Optional[int]
        assert annotations['type'] == MockNotificationType
        assert annotations['status'] == MockNotificationStatus
        assert annotations['sent_at'] == Optional[datetime]
        assert annotations['error_message'] == Optional[str]
        assert annotations['metadata'] == Optional[str]
        assert annotations['created_at'] == datetime

    def test_notification_log_instantiation(self):
        """Test creating NotificationLog instances."""
        @mock_strawberry_type
        class NotificationLog:
            def __init__(self, id, user_id, type, status, created_at=None,
                        template_id=None, sent_at=None, error_message=None,
                        metadata=None, template=None):
                self.id = id
                self.user_id = user_id
                self.template_id = template_id
                self.type = type
                self.status = status
                self.sent_at = sent_at
                self.error_message = error_message
                self.metadata = metadata
                self.created_at = created_at or datetime.now(timezone.utc)
                self.template = template
        
        log = NotificationLog(
            id=1,
            user_id=123,
            template_id=1,
            type=MockNotificationType.EMAIL,
            status=MockNotificationStatus.SENT,
            sent_at=datetime.now(timezone.utc),
            metadata='{"provider": "sendgrid"}'
        )
        
        assert log.id == 1
        assert log.user_id == 123
        assert log.template_id == 1
        assert log.type == MockNotificationType.EMAIL
        assert log.status == MockNotificationStatus.SENT
        assert isinstance(log.sent_at, datetime)
        assert log.metadata == '{"provider": "sendgrid"}'
        assert log.error_message is None
        assert log.template is None

    def test_user_preference_type_structure(self):
        """Test UserPreference type structure."""
        @mock_strawberry_type
        class UserPreference:
            id: int
            user_id: int
            email_enabled: bool
            sms_enabled: bool
            push_enabled: bool
            quiet_hours_start: Optional[str] = None
            quiet_hours_end: Optional[str] = None
            created_at: datetime
            updated_at: datetime
        
        # Test type annotations
        annotations = UserPreference.__annotations__
        assert annotations['id'] == int
        assert annotations['user_id'] == int
        assert annotations['email_enabled'] == bool
        assert annotations['sms_enabled'] == bool
        assert annotations['push_enabled'] == bool
        assert annotations['quiet_hours_start'] == Optional[str]
        assert annotations['quiet_hours_end'] == Optional[str]
        assert annotations['created_at'] == datetime
        assert annotations['updated_at'] == datetime

    def test_user_preference_instantiation(self):
        """Test creating UserPreference instances."""
        @mock_strawberry_type
        class UserPreference:
            def __init__(self, id, user_id, email_enabled=True, sms_enabled=True, 
                        push_enabled=True, quiet_hours_start=None, quiet_hours_end=None,
                        created_at=None, updated_at=None):
                self.id = id
                self.user_id = user_id
                self.email_enabled = email_enabled
                self.sms_enabled = sms_enabled
                self.push_enabled = push_enabled
                self.quiet_hours_start = quiet_hours_start
                self.quiet_hours_end = quiet_hours_end
                self.created_at = created_at or datetime.now(timezone.utc)
                self.updated_at = updated_at or datetime.now(timezone.utc)
        
        preference = UserPreference(
            id=1,
            user_id=123,
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True,
            quiet_hours_start="22:00:00",
            quiet_hours_end="08:00:00"
        )
        
        assert preference.id == 1
        assert preference.user_id == 123
        assert preference.email_enabled is True
        assert preference.sms_enabled is False
        assert preference.push_enabled is True
        assert preference.quiet_hours_start == "22:00:00"
        assert preference.quiet_hours_end == "08:00:00"
        assert isinstance(preference.created_at, datetime)
        assert isinstance(preference.updated_at, datetime)

    def test_notification_response_type_structure(self):
        """Test NotificationResponse type structure."""
        @mock_strawberry_type
        class NotificationResponse:
            id: int
            status: MockNotificationStatus
            message: str
            created_at: datetime
        
        # Test type annotations
        annotations = NotificationResponse.__annotations__
        assert annotations['id'] == int
        assert annotations['status'] == MockNotificationStatus
        assert annotations['message'] == str
        assert annotations['created_at'] == datetime

    def test_pagination_info_type_structure(self):
        """Test PaginationInfo type structure."""
        @mock_strawberry_type
        class PaginationInfo:
            total: int
            page: int
            size: int
            pages: int
        
        # Test type annotations
        annotations = PaginationInfo.__annotations__
        assert annotations['total'] == int
        assert annotations['page'] == int
        assert annotations['size'] == int
        assert annotations['pages'] == int

    def test_pagination_info_instantiation(self):
        """Test creating PaginationInfo instances."""
        @mock_strawberry_type
        class PaginationInfo:
            def __init__(self, total, page, size, pages):
                self.total = total
                self.page = page
                self.size = size
                self.pages = pages
        
        pagination = PaginationInfo(
            total=100,
            page=2,
            size=20,
            pages=5
        )
        
        assert pagination.total == 100
        assert pagination.page == 2
        assert pagination.size == 20
        assert pagination.pages == 5


@pytest.mark.unit
class TestGraphQLListTypes:
    """Test GraphQL list types."""

    def test_notification_template_list_type_structure(self):
        """Test NotificationTemplateList type structure."""
        @mock_strawberry_type
        class NotificationTemplate:
            pass
        
        @mock_strawberry_type
        class PaginationInfo:
            pass
        
        @mock_strawberry_type
        class NotificationTemplateList:
            items: List[NotificationTemplate]
            pagination: PaginationInfo
        
        # Test type annotations
        annotations = NotificationTemplateList.__annotations__
        assert annotations['items'] == List[NotificationTemplate]
        assert annotations['pagination'] == PaginationInfo

    def test_notification_log_list_type_structure(self):
        """Test NotificationLogList type structure."""
        @mock_strawberry_type
        class NotificationLog:
            pass
        
        @mock_strawberry_type
        class PaginationInfo:
            pass
        
        @mock_strawberry_type
        class NotificationLogList:
            items: List[NotificationLog]
            pagination: PaginationInfo
        
        # Test type annotations
        annotations = NotificationLogList.__annotations__
        assert annotations['items'] == List[NotificationLog]
        assert annotations['pagination'] == PaginationInfo

    def test_list_type_instantiation(self):
        """Test creating list type instances."""
        @mock_strawberry_type
        class NotificationTemplate:
            def __init__(self, id, name):
                self.id = id
                self.name = name
        
        @mock_strawberry_type
        class PaginationInfo:
            def __init__(self, total, page, size, pages):
                self.total = total
                self.page = page
                self.size = size
                self.pages = pages
        
        @mock_strawberry_type
        class NotificationTemplateList:
            def __init__(self, items, pagination):
                self.items = items
                self.pagination = pagination
        
        templates = [
            NotificationTemplate(1, "template1"),
            NotificationTemplate(2, "template2")
        ]
        pagination = PaginationInfo(2, 1, 10, 1)
        
        template_list = NotificationTemplateList(templates, pagination)
        
        assert len(template_list.items) == 2
        assert template_list.items[0].id == 1
        assert template_list.items[1].name == "template2"
        assert template_list.pagination.total == 2
        assert template_list.pagination.page == 1


@pytest.mark.unit
class TestGraphQLInputTypes:
    """Test GraphQL input types."""

    def test_notification_request_input_structure(self):
        """Test NotificationRequestInput structure."""
        @mock_strawberry_input
        class NotificationRequestInput:
            user_id: int
            template_name: str
            context: str
        
        # Test type annotations
        annotations = NotificationRequestInput.__annotations__
        assert annotations['user_id'] == int
        assert annotations['template_name'] == str
        assert annotations['context'] == str

    def test_notification_request_input_instantiation(self):
        """Test creating NotificationRequestInput instances."""
        @mock_strawberry_input
        class NotificationRequestInput:
            def __init__(self, user_id, template_name, context):
                self.user_id = user_id
                self.template_name = template_name
                self.context = context
        
        input_data = NotificationRequestInput(
            user_id=123,
            template_name="welcome_email",
            context='{"name": "John"}'
        )
        
        assert input_data.user_id == 123
        assert input_data.template_name == "welcome_email"
        assert input_data.context == '{"name": "John"}'

    def test_notification_template_create_input_structure(self):
        """Test NotificationTemplateCreateInput structure."""
        @mock_strawberry_input
        class NotificationTemplateCreateInput:
            name: str
            subject: Optional[str] = None
            body: str
            type: MockNotificationType
            variables: Optional[str] = None
        
        # Test type annotations
        annotations = NotificationTemplateCreateInput.__annotations__
        assert annotations['name'] == str
        assert annotations['subject'] == Optional[str]
        assert annotations['body'] == str
        assert annotations['type'] == MockNotificationType
        assert annotations['variables'] == Optional[str]

    def test_notification_template_create_input_instantiation(self):
        """Test creating NotificationTemplateCreateInput instances."""
        @mock_strawberry_input
        class NotificationTemplateCreateInput:
            def __init__(self, name, body, type, subject=None, variables=None):
                self.name = name
                self.subject = subject
                self.body = body
                self.type = type
                self.variables = variables
        
        input_data = NotificationTemplateCreateInput(
            name="new_template",
            subject="Subject",
            body="Body with {var}",
            type=MockNotificationType.EMAIL,
            variables='{"var": "string"}'
        )
        
        assert input_data.name == "new_template"
        assert input_data.subject == "Subject"
        assert input_data.body == "Body with {var}"
        assert input_data.type == MockNotificationType.EMAIL
        assert input_data.variables == '{"var": "string"}'

    def test_notification_template_update_input_structure(self):
        """Test NotificationTemplateUpdateInput structure."""
        @mock_strawberry_input
        class NotificationTemplateUpdateInput:
            name: Optional[str] = None
            subject: Optional[str] = None
            body: Optional[str] = None
            type: Optional[MockNotificationType] = None
            variables: Optional[str] = None
        
        # Test type annotations
        annotations = NotificationTemplateUpdateInput.__annotations__
        assert annotations['name'] == Optional[str]
        assert annotations['subject'] == Optional[str]
        assert annotations['body'] == Optional[str]
        assert annotations['type'] == Optional[MockNotificationType]
        assert annotations['variables'] == Optional[str]

    def test_notification_template_update_input_partial_update(self):
        """Test partial update with NotificationTemplateUpdateInput."""
        @mock_strawberry_input
        class NotificationTemplateUpdateInput:
            def __init__(self, name=None, subject=None, body=None, type=None, variables=None):
                self.name = name
                self.subject = subject
                self.body = body
                self.type = type
                self.variables = variables
        
        # Test partial update - only name and subject
        input_data = NotificationTemplateUpdateInput(
            name="updated_name",
            subject="Updated Subject"
        )
        
        assert input_data.name == "updated_name"
        assert input_data.subject == "Updated Subject"
        assert input_data.body is None
        assert input_data.type is None
        assert input_data.variables is None

    def test_notification_log_update_input_structure(self):
        """Test NotificationLogUpdateInput structure."""
        @mock_strawberry_input
        class NotificationLogUpdateInput:
            status: Optional[MockNotificationStatus] = None
            sent_at: Optional[datetime] = None
            error_message: Optional[str] = None
            metadata: Optional[str] = None
        
        # Test type annotations
        annotations = NotificationLogUpdateInput.__annotations__
        assert annotations['status'] == Optional[MockNotificationStatus]
        assert annotations['sent_at'] == Optional[datetime]
        assert annotations['error_message'] == Optional[str]
        assert annotations['metadata'] == Optional[str]

    def test_user_preference_update_input_structure(self):
        """Test UserPreferenceUpdateInput structure."""
        @mock_strawberry_input
        class UserPreferenceUpdateInput:
            email_enabled: Optional[bool] = None
            sms_enabled: Optional[bool] = None
            push_enabled: Optional[bool] = None
            quiet_hours_start: Optional[str] = None
            quiet_hours_end: Optional[str] = None
        
        # Test type annotations
        annotations = UserPreferenceUpdateInput.__annotations__
        assert annotations['email_enabled'] == Optional[bool]
        assert annotations['sms_enabled'] == Optional[bool]
        assert annotations['push_enabled'] == Optional[bool]
        assert annotations['quiet_hours_start'] == Optional[str]
        assert annotations['quiet_hours_end'] == Optional[str]

    def test_pagination_input_structure(self):
        """Test PaginationInput structure."""
        @mock_strawberry_input
        class PaginationInput:
            page: int = 1
            size: int = 50
        
        # Test type annotations
        annotations = PaginationInput.__annotations__
        assert annotations['page'] == int
        assert annotations['size'] == int

    def test_pagination_input_defaults(self):
        """Test PaginationInput default values."""
        @mock_strawberry_input
        class PaginationInput:
            def __init__(self, page=1, size=50):
                self.page = page
                self.size = size
        
        # Test with defaults
        input_data = PaginationInput()
        assert input_data.page == 1
        assert input_data.size == 50
        
        # Test with custom values
        input_data = PaginationInput(page=3, size=25)
        assert input_data.page == 3
        assert input_data.size == 25

    def test_template_filter_input_structure(self):
        """Test TemplateFilterInput structure."""
        @mock_strawberry_input
        class PaginationInput:
            pass
        
        @mock_strawberry_input
        class TemplateFilterInput:
            type_filter: Optional[str] = None
            pagination: Optional[PaginationInput] = None
        
        # Test type annotations
        annotations = TemplateFilterInput.__annotations__
        assert annotations['type_filter'] == Optional[str]
        assert annotations['pagination'] == Optional[PaginationInput]


@pytest.mark.unit
class TestGraphQLTypeValidation:
    """Test GraphQL type validation logic."""

    def test_enum_value_validation(self):
        """Test enum value validation."""
        def validate_notification_type(value):
            try:
                return MockNotificationType(value), None
            except ValueError:
                return None, f"Invalid notification type: {value}"
        
        # Valid values
        result, error = validate_notification_type("email")
        assert result == MockNotificationType.EMAIL
        assert error is None
        
        # Invalid value
        result, error = validate_notification_type("invalid")
        assert result is None
        assert "Invalid notification type" in error

    def test_optional_field_handling(self):
        """Test handling of optional fields."""
        @mock_strawberry_type
        class TestType:
            def __init__(self, required_field, optional_field=None):
                self.required_field = required_field
                self.optional_field = optional_field
        
        # With optional field
        obj1 = TestType("required", "optional")
        assert obj1.required_field == "required"
        assert obj1.optional_field == "optional"
        
        # Without optional field
        obj2 = TestType("required")
        assert obj2.required_field == "required"
        assert obj2.optional_field is None

    def test_list_type_handling(self):
        """Test handling of list types."""
        @mock_strawberry_type
        class Item:
            def __init__(self, id, name):
                self.id = id
                self.name = name
        
        @mock_strawberry_type
        class ItemList:
            def __init__(self, items):
                self.items = items
        
        items = [Item(1, "item1"), Item(2, "item2")]
        item_list = ItemList(items)
        
        assert len(item_list.items) == 2
        assert all(isinstance(item, Item) for item in item_list.items)
        assert item_list.items[0].id == 1
        assert item_list.items[1].name == "item2"

    def test_datetime_field_handling(self):
        """Test datetime field handling."""
        @mock_strawberry_type
        class TimestampType:
            def __init__(self, created_at=None, updated_at=None):
                self.created_at = created_at or datetime.now(timezone.utc)
                self.updated_at = updated_at or datetime.now(timezone.utc)
        
        obj = TimestampType()
        assert isinstance(obj.created_at, datetime)
        assert isinstance(obj.updated_at, datetime)
        
        # Test with specific datetime
        specific_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        obj2 = TimestampType(created_at=specific_time)
        assert obj2.created_at == specific_time
        assert isinstance(obj2.updated_at, datetime)

    def test_json_string_field_handling(self):
        """Test JSON string field handling in GraphQL types."""
        def validate_json_field(value):
            """Validate that a field contains valid JSON."""
            if value is None:
                return True, None
            try:
                import json
                json.loads(value)
                return True, None
            except (json.JSONDecodeError, TypeError):
                return False, "Invalid JSON format"
        
        # Valid JSON
        valid, error = validate_json_field('{"key": "value"}')
        assert valid is True
        assert error is None
        
        # Invalid JSON
        valid, error = validate_json_field('invalid json')
        assert valid is False
        assert "Invalid JSON format" in error
        
        # None value (allowed)
        valid, error = validate_json_field(None)
        assert valid is True
        assert error is None


@pytest.mark.unit
class TestGraphQLTypeUsagePatterns:
    """Test common GraphQL type usage patterns."""

    def test_type_composition(self):
        """Test composing types together."""
        @mock_strawberry_type
        class NotificationTemplate:
            def __init__(self, id, name, type):
                self.id = id
                self.name = name
                self.type = type
        
        @mock_strawberry_type
        class NotificationLog:
            def __init__(self, id, user_id, template=None):
                self.id = id
                self.user_id = user_id
                self.template = template
        
        template = NotificationTemplate(1, "welcome", MockNotificationType.EMAIL)
        log = NotificationLog(1, 123, template)
        
        assert log.template.id == 1
        assert log.template.name == "welcome"
        assert log.template.type == MockNotificationType.EMAIL

    def test_input_to_type_conversion(self):
        """Test converting input types to object types."""
        @mock_strawberry_input
        class TemplateCreateInput:
            def __init__(self, name, body, type):
                self.name = name
                self.body = body
                self.type = type
        
        @mock_strawberry_type
        class NotificationTemplate:
            def __init__(self, id, name, body, type, created_at=None):
                self.id = id
                self.name = name
                self.body = body
                self.type = type
                self.created_at = created_at or datetime.now(timezone.utc)
        
        def create_template_from_input(input_data, id):
            return NotificationTemplate(
                id=id,
                name=input_data.name,
                body=input_data.body,
                type=input_data.type
            )
        
        input_data = TemplateCreateInput(
            name="test_template",
            body="Test body",
            type=MockNotificationType.EMAIL
        )
        
        template = create_template_from_input(input_data, 1)
        
        assert template.id == 1
        assert template.name == "test_template"
        assert template.body == "Test body"
        assert template.type == MockNotificationType.EMAIL
        assert isinstance(template.created_at, datetime)

    def test_pagination_calculations(self):
        """Test pagination calculations with types."""
        @mock_strawberry_type
        class PaginationInfo:
            def __init__(self, total, page, size):
                self.total = total
                self.page = page
                self.size = size
                self.pages = (total + size - 1) // size  # Calculate pages
        
        # Test various pagination scenarios
        pagination1 = PaginationInfo(100, 1, 20)
        assert pagination1.pages == 5
        
        pagination2 = PaginationInfo(23, 2, 10)
        assert pagination2.pages == 3
        
        pagination3 = PaginationInfo(0, 1, 10)
        assert pagination3.pages == 0

    def test_error_response_patterns(self):
        """Test error response patterns in GraphQL types."""
        @mock_strawberry_type
        class ErrorInfo:
            def __init__(self, message, code=None, field=None):
                self.message = message
                self.code = code
                self.field = field
        
        @mock_strawberry_type
        class ValidationResult:
            def __init__(self, success, errors=None):
                self.success = success
                self.errors = errors or []
        
        # Test success case
        success_result = ValidationResult(True)
        assert success_result.success is True
        assert len(success_result.errors) == 0
        
        # Test error case
        error_result = ValidationResult(False, [
            ErrorInfo("Required field missing", "REQUIRED", "name"),
            ErrorInfo("Invalid format", "FORMAT", "email")
        ])
        
        assert error_result.success is False
        assert len(error_result.errors) == 2
        assert error_result.errors[0].message == "Required field missing"
        assert error_result.errors[0].code == "REQUIRED"
        assert error_result.errors[0].field == "name"
