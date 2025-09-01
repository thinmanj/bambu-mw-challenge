"""
Unit tests for core models.
"""

import pytest
from datetime import datetime, time
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.exc import IntegrityError

from core.models import (
    NotificationType, NotificationStatus,
    NotificationTemplate, NotificationLog, UserPreference
)


@pytest.mark.unit
class TestEnums:
    """Test cases for enum classes."""

    def test_notification_type_enum(self):
        """Test NotificationType enum values."""
        assert NotificationType.EMAIL == "email"
        assert NotificationType.SMS == "sms"
        assert NotificationType.PUSH == "push"
        
        # Test enum membership
        assert "email" in NotificationType
        assert "sms" in NotificationType
        assert "push" in NotificationType
        assert "invalid" not in NotificationType

    def test_notification_status_enum(self):
        """Test NotificationStatus enum values."""
        assert NotificationStatus.PENDING == "pending"
        assert NotificationStatus.SENT == "sent"
        assert NotificationStatus.FAILED == "failed"
        assert NotificationStatus.BOUNCED == "bounced"
        
        # Test enum membership
        assert "pending" in NotificationStatus
        assert "sent" in NotificationStatus
        assert "failed" in NotificationStatus
        assert "bounced" in NotificationStatus
        assert "invalid" not in NotificationStatus


@pytest.mark.unit
class TestNotificationTemplate:
    """Test cases for NotificationTemplate model."""

    def test_notification_template_instantiation(self):
        """Test instantiating a notification template model."""
        template = NotificationTemplate(
            name="test_template",
            subject="Test Subject",
            body="Test body with {variable}",
            type="email",
            variables={"variable": "string"}
        )
        
        assert template.name == "test_template"
        assert template.subject == "Test Subject"
        assert template.body == "Test body with {variable}"
        assert template.type == "email"
        assert template.variables == {"variable": "string"}

    def test_notification_template_table_name(self):
        """Test that the table name is correct."""
        assert NotificationTemplate.__tablename__ == "notification_templates"
    
    def test_notification_template_columns(self):
        """Test that the model has the expected columns."""
        # Check that key columns exist
        assert hasattr(NotificationTemplate, "id")
        assert hasattr(NotificationTemplate, "name")
        assert hasattr(NotificationTemplate, "subject")
        assert hasattr(NotificationTemplate, "body")
        assert hasattr(NotificationTemplate, "type")
        assert hasattr(NotificationTemplate, "variables")
        assert hasattr(NotificationTemplate, "created_at")
        assert hasattr(NotificationTemplate, "updated_at")
        
        # Check column properties
        assert NotificationTemplate.name.primary_key is False
        assert NotificationTemplate.name.nullable is False
        assert NotificationTemplate.subject.nullable is True
        assert NotificationTemplate.body.nullable is False
        assert NotificationTemplate.type.nullable is False

    def test_notification_template_relationships(self):
        """Test that the model has the expected relationships."""
        assert hasattr(NotificationTemplate, "notification_logs")
    
    def test_notification_template_constraints(self):
        """Test that the model has the expected constraints."""
        # Check for type constraint
        constraints = NotificationTemplate.__table_args__
        type_constraint_exists = False
        
        for constraint in constraints:
            if hasattr(constraint, "name") and constraint.name == "check_notification_template_type":
                type_constraint_exists = True
                break
        
        assert type_constraint_exists is True


@pytest.mark.unit
class TestNotificationLog:
    """Test cases for NotificationLog model."""

    def test_notification_log_instantiation(self):
        """Test instantiating a notification log model."""
        log = NotificationLog(
            user_id=123,
            type="email",
            status="pending",
            notification_metadata={"recipient": "test@example.com"}
        )
        
        assert log.user_id == 123
        assert log.type == "email"
        assert log.status == "pending"
        assert log.notification_metadata == {"recipient": "test@example.com"}
        # Default/unset values
        assert log.id is None  # Set by database
        assert log.template_id is None
        assert log.sent_at is None
        assert log.error_message is None
        assert log.created_at is None  # Set by database

    def test_notification_log_table_name(self):
        """Test that the table name is correct."""
        assert NotificationLog.__tablename__ == "notification_logs"
    
    def test_notification_log_columns(self):
        """Test that the model has the expected columns."""
        # Check that key columns exist
        assert hasattr(NotificationLog, "id")
        assert hasattr(NotificationLog, "user_id")
        assert hasattr(NotificationLog, "template_id")
        assert hasattr(NotificationLog, "type")
        assert hasattr(NotificationLog, "status")
        assert hasattr(NotificationLog, "sent_at")
        assert hasattr(NotificationLog, "error_message")
        assert hasattr(NotificationLog, "notification_metadata")
        assert hasattr(NotificationLog, "created_at")
        
        # Check column properties
        assert NotificationLog.user_id.nullable is False
        assert NotificationLog.template_id.nullable is True
        assert NotificationLog.type.nullable is False
        assert NotificationLog.status.nullable is False
        assert NotificationLog.sent_at.nullable is True
        assert NotificationLog.error_message.nullable is True
        assert NotificationLog.notification_metadata.nullable is True

    def test_notification_log_relationships(self):
        """Test that the model has the expected relationships."""
        assert hasattr(NotificationLog, "template")
    
    def test_notification_log_constraints(self):
        """Test that the model has the expected constraints."""
        # Check for type and status constraints
        constraints = NotificationLog.__table_args__
        constraint_names = []
        
        for constraint in constraints:
            if hasattr(constraint, "name"):
                constraint_names.append(constraint.name)
        
        assert "check_notification_log_type" in constraint_names
        assert "check_notification_log_status" in constraint_names


@pytest.mark.unit
class TestUserPreference:
    """Test cases for UserPreference model."""

    def test_user_preference_instantiation(self):
        """Test instantiating a user preference model."""
        preference = UserPreference(
            user_id=123,
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0)
        )
        
        assert preference.user_id == 123
        assert preference.email_enabled is True
        assert preference.sms_enabled is False
        assert preference.push_enabled is True
        assert preference.quiet_hours_start == time(22, 0)
        assert preference.quiet_hours_end == time(8, 0)
        # Database-set values
        assert preference.id is None
        assert preference.created_at is None
        assert preference.updated_at is None

    def test_user_preference_table_name(self):
        """Test that the table name is correct."""
        assert UserPreference.__tablename__ == "user_preferences"
    
    def test_user_preference_columns(self):
        """Test that the model has the expected columns."""
        # Check that key columns exist
        assert hasattr(UserPreference, "id")
        assert hasattr(UserPreference, "user_id")
        assert hasattr(UserPreference, "email_enabled")
        assert hasattr(UserPreference, "sms_enabled")
        assert hasattr(UserPreference, "push_enabled")
        assert hasattr(UserPreference, "quiet_hours_start")
        assert hasattr(UserPreference, "quiet_hours_end")
        assert hasattr(UserPreference, "updated_at")
        assert hasattr(UserPreference, "created_at")
        
        # Check column properties
        assert UserPreference.user_id.nullable is False
        assert UserPreference.quiet_hours_start.nullable is True
        assert UserPreference.quiet_hours_end.nullable is True

    def test_user_preference_unique_user_id_column(self):
        """Test that user_id column has unique constraint."""
        # Check that user_id column has unique constraint
        assert UserPreference.user_id.unique is True




@pytest.mark.unit
class TestModelInstantiation:
    """Test cases for model instantiation without database."""

    def test_notification_template_instantiation(self):
        """Test creating a notification template instance."""
        template = NotificationTemplate(
            name="test_template",
            subject="Test Subject",
            body="Test body with {variable}",
            type="email",
            variables={"variable": "string"}
        )
        
        assert template.name == "test_template"
        assert template.subject == "Test Subject"
        assert template.body == "Test body with {variable}"
        assert template.type == "email"
        assert template.variables == {"variable": "string"}
        # ID should be None until saved to database
        assert template.id is None
        assert template.created_at is None  # Set by database
        assert template.updated_at is None  # Set by database

    def test_notification_template_with_variables(self):
        """Test template with various variable types."""
        variables = {
            "user_name": "string",
            "amount": "number",
            "is_active": "boolean"
        }
        
        template = NotificationTemplate(
            name="complex_template",
            body="Hello {user_name}, your balance is {amount}",
            type="email",
            variables=variables
        )
        
        assert template.variables == variables
        assert template.name == "complex_template"

    def test_notification_log_instantiation(self):
        """Test creating a notification log instance."""
        log = NotificationLog(
            user_id=123,
            type="email",
            status="pending",
            notification_metadata={"recipient": "test@example.com"}
        )
        
        assert log.user_id == 123
        assert log.type == "email"
        assert log.status == "pending"
        assert log.notification_metadata == {"recipient": "test@example.com"}
        # Default values
        assert log.id is None  # Set by database
        assert log.template_id is None
        assert log.sent_at is None
        assert log.error_message is None
        assert log.created_at is None  # Set by database

    def test_notification_log_metadata(self):
        """Test notification metadata handling."""
        metadata = {
            "recipient": "test@example.com",
            "subject": "Test Subject",
            "attempts": 1,
            "provider": "sendgrid"
        }
        
        log = NotificationLog(
            user_id=123,
            type="email",
            status="pending",
            notification_metadata=metadata
        )
        
        assert log.notification_metadata == metadata

    def test_user_preference_instantiation(self):
        """Test creating user preferences."""
        preference = UserPreference(
            user_id=123,
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0)
        )
        
        assert preference.user_id == 123
        assert preference.email_enabled is True
        assert preference.sms_enabled is False
        assert preference.push_enabled is True
        assert preference.quiet_hours_start == time(22, 0)
        assert preference.quiet_hours_end == time(8, 0)
        # ID and timestamps set by database
        assert preference.id is None
        assert preference.created_at is None
        assert preference.updated_at is None

    def test_user_preference_defaults(self):
        """Test default values for user preferences."""
        preference = UserPreference(user_id=456)
        
        # These should be set as column defaults, but won't show up until saved
        assert preference.user_id == 456
        # The defaults are defined at the database level, so they won't be 
        # set until the instance is saved to the database
        assert preference.email_enabled is None  # Will be True after DB save
        assert preference.sms_enabled is None    # Will be True after DB save
        assert preference.push_enabled is None   # Will be True after DB save
        assert preference.quiet_hours_start is None
        assert preference.quiet_hours_end is None


@pytest.mark.unit
class TestModelTableNames:
    """Test that models have correct table names."""

    def test_notification_template_table_name(self):
        """Test NotificationTemplate table name."""
        assert NotificationTemplate.__tablename__ == "notification_templates"

    def test_notification_log_table_name(self):
        """Test NotificationLog table name."""
        assert NotificationLog.__tablename__ == "notification_logs"

    def test_user_preference_table_name(self):
        """Test UserPreference table name."""
        assert UserPreference.__tablename__ == "user_preferences"


@pytest.mark.unit
class TestModelConstraints:
    """Test model constraints are defined properly."""

    def test_notification_template_constraints(self):
        """Test NotificationTemplate has proper constraints."""
        # Check that constraints exist
        constraints = NotificationTemplate.__table_args__
        assert len(constraints) > 0
        
        # Check for type constraint
        type_constraint_found = False
        for constraint in constraints:
            if hasattr(constraint, 'name') and constraint.name == 'check_notification_template_type':
                type_constraint_found = True
                break
        assert type_constraint_found

    def test_notification_log_constraints(self):
        """Test NotificationLog has proper constraints."""
        # Check that constraints exist
        constraints = NotificationLog.__table_args__
        assert len(constraints) > 0
        
        # Check for type and status constraints
        constraint_names = []
        for constraint in constraints:
            if hasattr(constraint, 'name'):
                constraint_names.append(constraint.name)
        
        assert 'check_notification_log_type' in constraint_names
        assert 'check_notification_log_status' in constraint_names


@pytest.mark.unit
class TestModelRelationshipDefinitions:
    """Test that model relationships are defined correctly."""

    def test_template_has_logs_relationship(self):
        """Test that NotificationTemplate has notification_logs relationship."""
        # Check that the relationship is defined
        assert hasattr(NotificationTemplate, 'notification_logs')
        
        # Check relationship properties
        rel = NotificationTemplate.notification_logs
        assert rel is not None

    def test_log_has_template_relationship(self):
        """Test that NotificationLog has template relationship."""
        # Check that the relationship is defined
        assert hasattr(NotificationLog, 'template')
        
        # Check relationship properties
        rel = NotificationLog.template
        assert rel is not None
