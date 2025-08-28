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

    @pytest.mark.asyncio
    async def test_notification_template_creation(self, async_db_session):
        """Test creating a notification template."""
        template = NotificationTemplate(
            name="test_template",
            subject="Test Subject",
            body="Test body with {variable}",
            type="email",
            variables={"variable": "string"}
        )
        
        async_db_session.add(template)
        await async_db_session.commit()
        await async_db_session.refresh(template)
        
        assert template.id is not None
        assert template.name == "test_template"
        assert template.subject == "Test Subject"
        assert template.body == "Test body with {variable}"
        assert template.type == "email"
        assert template.variables == {"variable": "string"}
        assert template.created_at is not None
        assert template.updated_at is not None

    @pytest.mark.asyncio
    async def test_notification_template_unique_name_constraint(self, async_db_session):
        """Test that template names must be unique."""
        template1 = NotificationTemplate(
            name="duplicate_name",
            body="Body 1",
            type="email"
        )
        template2 = NotificationTemplate(
            name="duplicate_name",
            body="Body 2",
            type="sms"
        )
        
        async_db_session.add(template1)
        await async_db_session.commit()
        
        async_db_session.add(template2)
        
        with pytest.raises(IntegrityError):
            await async_db_session.commit()

    @pytest.mark.asyncio
    async def test_notification_template_type_constraint(self, async_db_session):
        """Test that template type must be valid."""
        template = NotificationTemplate(
            name="invalid_type_template",
            body="Test body",
            type="invalid_type"
        )
        
        async_db_session.add(template)
        
        with pytest.raises(IntegrityError):
            await async_db_session.commit()

    @pytest.mark.asyncio
    async def test_notification_template_required_fields(self, async_db_session):
        """Test that required fields must be provided."""
        # Missing name
        with pytest.raises((IntegrityError, TypeError)):
            template = NotificationTemplate(
                body="Test body",
                type="email"
            )
            async_db_session.add(template)
            await async_db_session.commit()

    @pytest.mark.asyncio
    async def test_notification_template_relationships(self, async_db_session):
        """Test template relationships with logs."""
        # Create template
        template = NotificationTemplate(
            name="test_template_with_logs",
            body="Test body",
            type="email"
        )
        async_db_session.add(template)
        await async_db_session.commit()
        await async_db_session.refresh(template)
        
        # Create related log
        log = NotificationLog(
            user_id=123,
            template_id=template.id,
            type="email",
            status="pending"
        )
        async_db_session.add(log)
        await async_db_session.commit()
        
        # Test relationship loading
        await async_db_session.refresh(template)
        assert len(template.notification_logs) == 1
        assert template.notification_logs[0].user_id == 123

    @pytest.mark.asyncio
    async def test_notification_template_optional_subject(self, async_db_session):
        """Test that subject is optional for templates."""
        template = NotificationTemplate(
            name="no_subject_template",
            body="Test body without subject",
            type="sms",
            subject=None
        )
        
        async_db_session.add(template)
        await async_db_session.commit()
        await async_db_session.refresh(template)
        
        assert template.subject is None
        assert template.body == "Test body without subject"


@pytest.mark.unit
class TestNotificationLog:
    """Test cases for NotificationLog model."""

    @pytest.mark.asyncio
    async def test_notification_log_creation(self, async_db_session):
        """Test creating a notification log."""
        log = NotificationLog(
            user_id=123,
            type="email",
            status="pending",
            notification_metadata={"recipient": "test@example.com"}
        )
        
        async_db_session.add(log)
        await async_db_session.commit()
        await async_db_session.refresh(log)
        
        assert log.id is not None
        assert log.user_id == 123
        assert log.type == "email"
        assert log.status == "pending"
        assert log.sent_at is None
        assert log.error_message is None
        assert log.notification_metadata == {"recipient": "test@example.com"}
        assert log.created_at is not None

    @pytest.mark.asyncio
    async def test_notification_log_with_template(self, async_db_session):
        """Test creating a log with template reference."""
        # Create template first
        template = NotificationTemplate(
            name="log_template",
            body="Template for log test",
            type="email"
        )
        async_db_session.add(template)
        await async_db_session.commit()
        await async_db_session.refresh(template)
        
        # Create log with template reference
        log = NotificationLog(
            user_id=456,
            template_id=template.id,
            type="email",
            status="sent",
            sent_at=datetime.utcnow()
        )
        
        async_db_session.add(log)
        await async_db_session.commit()
        await async_db_session.refresh(log)
        
        assert log.template_id == template.id
        assert log.template.name == "log_template"
        assert log.sent_at is not None

    @pytest.mark.asyncio
    async def test_notification_log_type_constraint(self, async_db_session):
        """Test that log type must be valid."""
        log = NotificationLog(
            user_id=123,
            type="invalid_type",
            status="pending"
        )
        
        async_db_session.add(log)
        
        with pytest.raises(IntegrityError):
            await async_db_session.commit()

    @pytest.mark.asyncio
    async def test_notification_log_status_constraint(self, async_db_session):
        """Test that log status must be valid."""
        log = NotificationLog(
            user_id=123,
            type="email",
            status="invalid_status"
        )
        
        async_db_session.add(log)
        
        with pytest.raises(IntegrityError):
            await async_db_session.commit()

    @pytest.mark.asyncio
    async def test_notification_log_default_status(self, async_db_session):
        """Test that log status defaults to 'pending'."""
        log = NotificationLog(
            user_id=123,
            type="email"
        )
        
        async_db_session.add(log)
        await async_db_session.commit()
        await async_db_session.refresh(log)
        
        assert log.status == "pending"

    @pytest.mark.asyncio
    async def test_notification_log_error_handling(self, async_db_session):
        """Test logging with error information."""
        log = NotificationLog(
            user_id=123,
            type="email",
            status="failed",
            error_message="SMTP connection failed"
        )
        
        async_db_session.add(log)
        await async_db_session.commit()
        await async_db_session.refresh(log)
        
        assert log.status == "failed"
        assert log.error_message == "SMTP connection failed"
        assert log.sent_at is None

    @pytest.mark.asyncio
    async def test_notification_log_required_fields(self, async_db_session):
        """Test that required fields must be provided."""
        # Missing user_id
        with pytest.raises((IntegrityError, TypeError)):
            log = NotificationLog(
                type="email",
                status="pending"
            )
            async_db_session.add(log)
            await async_db_session.commit()


@pytest.mark.unit
class TestUserPreference:
    """Test cases for UserPreference model."""

    @pytest.mark.asyncio
    async def test_user_preference_creation(self, async_db_session):
        """Test creating user preferences."""
        preference = UserPreference(
            user_id=123,
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0)
        )
        
        async_db_session.add(preference)
        await async_db_session.commit()
        await async_db_session.refresh(preference)
        
        assert preference.id is not None
        assert preference.user_id == 123
        assert preference.email_enabled is True
        assert preference.sms_enabled is False
        assert preference.push_enabled is True
        assert preference.quiet_hours_start == time(22, 0)
        assert preference.quiet_hours_end == time(8, 0)
        assert preference.created_at is not None
        assert preference.updated_at is not None

    @pytest.mark.asyncio
    async def test_user_preference_defaults(self, async_db_session):
        """Test default values for user preferences."""
        preference = UserPreference(user_id=456)
        
        async_db_session.add(preference)
        await async_db_session.commit()
        await async_db_session.refresh(preference)
        
        assert preference.email_enabled is True
        assert preference.sms_enabled is True
        assert preference.push_enabled is True
        assert preference.quiet_hours_start is None
        assert preference.quiet_hours_end is None

    @pytest.mark.asyncio
    async def test_user_preference_unique_user_id(self, async_db_session):
        """Test that user_id must be unique."""
        preference1 = UserPreference(user_id=789)
        preference2 = UserPreference(user_id=789)
        
        async_db_session.add(preference1)
        await async_db_session.commit()
        
        async_db_session.add(preference2)
        
        with pytest.raises(IntegrityError):
            await async_db_session.commit()

    @pytest.mark.asyncio
    async def test_user_preference_quiet_hours_none(self, async_db_session):
        """Test that quiet hours can be None."""
        preference = UserPreference(
            user_id=999,
            quiet_hours_start=None,
            quiet_hours_end=None
        )
        
        async_db_session.add(preference)
        await async_db_session.commit()
        await async_db_session.refresh(preference)
        
        assert preference.quiet_hours_start is None
        assert preference.quiet_hours_end is None

    @pytest.mark.asyncio
    async def test_user_preference_partial_quiet_hours(self, async_db_session):
        """Test quiet hours with only one value set."""
        preference = UserPreference(
            user_id=1000,
            quiet_hours_start=time(23, 30),
            quiet_hours_end=None
        )
        
        async_db_session.add(preference)
        await async_db_session.commit()
        await async_db_session.refresh(preference)
        
        assert preference.quiet_hours_start == time(23, 30)
        assert preference.quiet_hours_end is None

    @pytest.mark.asyncio
    async def test_user_preference_boolean_fields(self, async_db_session):
        """Test boolean notification enable/disable fields."""
        preference = UserPreference(
            user_id=1001,
            email_enabled=False,
            sms_enabled=False,
            push_enabled=False
        )
        
        async_db_session.add(preference)
        await async_db_session.commit()
        await async_db_session.refresh(preference)
        
        assert preference.email_enabled is False
        assert preference.sms_enabled is False
        assert preference.push_enabled is False

    @pytest.mark.asyncio
    async def test_user_preference_required_user_id(self, async_db_session):
        """Test that user_id is required."""
        with pytest.raises((IntegrityError, TypeError)):
            preference = UserPreference(
                email_enabled=True,
                sms_enabled=True,
                push_enabled=True
            )
            async_db_session.add(preference)
            await async_db_session.commit()


@pytest.mark.unit
class TestModelRelationships:
    """Test cases for model relationships."""

    @pytest.mark.asyncio
    async def test_template_log_relationship(self, async_db_session):
        """Test the relationship between templates and logs."""
        # Create template
        template = NotificationTemplate(
            name="relationship_test",
            body="Test relationship",
            type="email"
        )
        async_db_session.add(template)
        await async_db_session.commit()
        await async_db_session.refresh(template)
        
        # Create multiple logs for the template
        log1 = NotificationLog(
            user_id=1,
            template_id=template.id,
            type="email",
            status="sent"
        )
        log2 = NotificationLog(
            user_id=2,
            template_id=template.id,
            type="email",
            status="pending"
        )
        
        async_db_session.add_all([log1, log2])
        await async_db_session.commit()
        
        # Refresh and test relationships
        await async_db_session.refresh(template)
        await async_db_session.refresh(log1)
        await async_db_session.refresh(log2)
        
        # Test forward relationship (template -> logs)
        assert len(template.notification_logs) == 2
        log_user_ids = [log.user_id for log in template.notification_logs]
        assert 1 in log_user_ids
        assert 2 in log_user_ids
        
        # Test reverse relationship (log -> template)
        assert log1.template.name == "relationship_test"
        assert log2.template.name == "relationship_test"

    @pytest.mark.asyncio
    async def test_log_without_template(self, async_db_session):
        """Test that logs can exist without templates."""
        log = NotificationLog(
            user_id=123,
            type="email",
            status="sent",
            template_id=None
        )
        
        async_db_session.add(log)
        await async_db_session.commit()
        await async_db_session.refresh(log)
        
        assert log.template_id is None
        assert log.template is None


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
