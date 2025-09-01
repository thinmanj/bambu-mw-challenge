"""
Comprehensive unit tests for email adapter.
"""

import pytest
from unittest.mock import patch, MagicMock
from adapters.email import EmailProvider
from core.resilience.retry import RetryableError, NonRetryableError


@pytest.fixture
def email_provider():
    """Create email provider for testing."""
    return EmailProvider()


@pytest.fixture
def valid_email_context():
    """Valid email context for testing."""
    return {
        'to_email': 'test@example.com',
        'subject': 'Test Subject',
        'body': 'Test email body'
    }


@pytest.mark.unit
class TestEmailProvider:
    """Test cases for EmailProvider."""

    def test_email_provider_initialization(self, email_provider):
        """Test that EmailProvider initializes correctly."""
        assert email_provider is not None
        assert hasattr(email_provider, 'send')
        assert email_provider.adapter_name == "email"

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_email_success(self, mock_random, email_provider, valid_email_context):
        """Test successful email sending."""
        result = email_provider.send(valid_email_context)
        
        assert result is not None
        assert result['success'] is True
        assert result['provider'] == 'email'
        assert result['recipient'] == valid_email_context['to_email']
        assert result['subject'] == valid_email_context['subject']
        assert 'message_id' in result
        assert result['message_id'].startswith('email_msg_')

    @patch('random.random', return_value=0.5)  # No random failures  
    def test_send_email_with_recipient_fallback(self, mock_random, email_provider):
        """Test email sending with recipient field fallback."""
        context = {
            'recipient': 'test@example.com',
            'subject': 'Test Subject',
            'body': 'Test body'
        }
        
        result = email_provider.send(context)
        
        assert result['success'] is True
        assert result['recipient'] == 'test@example.com'

    def test_send_email_missing_recipient(self, email_provider):
        """Test email sending fails when recipient is missing."""
        context = {
            'subject': 'Test Subject',
            'body': 'Test body'
            # Missing to_email and recipient
        }
        
        with pytest.raises(NonRetryableError) as exc_info:
            email_provider.send(context)
        
        assert "Missing recipient" in str(exc_info.value)

    def test_send_email_missing_message(self, email_provider):
        """Test email sending fails when message is missing."""
        context = {
            'to_email': 'test@example.com'
            # Missing subject, body, and message
        }
        
        with pytest.raises(NonRetryableError) as exc_info:
            email_provider.send(context)
        
        assert "Missing message" in str(exc_info.value)

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_email_with_default_subject(self, mock_random, email_provider):
        """Test email sending with default subject."""
        context = {
            'to_email': 'test@example.com',
            'body': 'Test body'
            # Missing subject - should use default
        }
        
        result = email_provider.send(context)
        
        assert result['success'] is True
        assert result['subject'] == 'No Subject'

    def test_send_email_invalid_format(self, email_provider):
        """Test email sending fails with invalid email format."""
        context = {
            'to_email': 'invalid-email',  # No @ symbol
            'subject': 'Test',
            'body': 'Test body'
        }
        
        with pytest.raises(NonRetryableError) as exc_info:
            email_provider.send(context)
        
        assert "Invalid email address format" in str(exc_info.value)

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_email_message_id_generation(self, mock_random, email_provider, valid_email_context):
        """Test that message ID is generated consistently."""
        result1 = email_provider.send(valid_email_context)
        result2 = email_provider.send(valid_email_context)
        
        # Same context should generate same message ID
        assert result1['message_id'] == result2['message_id']

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_email_different_contexts_different_ids(self, mock_random, email_provider):
        """Test that different contexts generate different message IDs."""
        context1 = {
            'to_email': 'test1@example.com',
            'subject': 'Subject 1',
            'body': 'Body 1'
        }
        context2 = {
            'to_email': 'test2@example.com',
            'subject': 'Subject 2',
            'body': 'Body 2'
        }
        
        result1 = email_provider.send(context1)
        result2 = email_provider.send(context2)
        
        assert result1['message_id'] != result2['message_id']

    @patch('random.random', return_value=0.5)  # No random failures
    @patch('adapters.email.logger')
    def test_send_email_logging(self, mock_logger, mock_random, email_provider, valid_email_context):
        """Test that email sending is properly logged."""
        email_provider.send(valid_email_context)
        
        # Check that info log was called
        mock_logger.info.assert_called()
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        
        # Should have sending logs (initialization logs are from constructor)
        assert any('Sending email to' in call for call in log_calls)

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_email_comprehensive_functionality(self, mock_random, email_provider):
        """Test comprehensive email functionality including edge cases."""
        # Test with various valid contexts
        test_cases = [
            {
                'context': {
                    'to_email': 'user@example.com',
                    'subject': 'Test Subject',
                    'body': 'Test body'
                },
                'expected_recipient': 'user@example.com',
                'expected_subject': 'Test Subject'
            },
            {
                'context': {
                    'recipient': 'fallback@example.com',
                    'subject': 'Fallback Test',
                    'message': 'Message field test'
                },
                'expected_recipient': 'fallback@example.com',
                'expected_subject': 'Fallback Test'
            },
            {
                'context': {
                    'to_email': 'minimal@example.com',
                    'body': 'Minimal context'
                },
                'expected_recipient': 'minimal@example.com',
                'expected_subject': 'No Subject'
            }
        ]
        
        for case in test_cases:
            result = email_provider.send(case['context'])
            assert result['success'] is True
            assert result['recipient'] == case['expected_recipient']
            assert result['subject'] == case['expected_subject']
            assert result['provider'] == 'email'
            assert 'message_id' in result

    def test_send_email_invalid_context_type(self, email_provider):
        """Test email sending fails with invalid context type."""
        with pytest.raises(NonRetryableError) as exc_info:
            email_provider.send("invalid_context")
        
        assert "Invalid context" in str(exc_info.value)

    def test_send_email_empty_context(self, email_provider):
        """Test email sending fails with empty context."""
        with pytest.raises(NonRetryableError) as exc_info:
            email_provider.send({})
        
        # Base adapter validates context first, then recipient
        assert "Missing recipient" in str(exc_info.value)

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_email_response_structure(self, mock_random, email_provider, valid_email_context):
        """Test that email response has correct structure."""
        result = email_provider.send(valid_email_context)
        
        required_fields = ['success', 'message_id', 'provider', 'recipient', 'subject']
        for field in required_fields:
            assert field in result

        # Check data types
        assert isinstance(result['success'], bool)
        assert isinstance(result['message_id'], str)
        assert isinstance(result['provider'], str)
        assert isinstance(result['recipient'], str)
        assert isinstance(result['subject'], str)

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_email_message_body_fallback(self, mock_random, email_provider):
        """Test email sending with message field as body fallback."""
        context = {
            'to_email': 'test@example.com',
            'subject': 'Test Subject',
            'message': 'Test message content'  # Using message instead of body
        }
        
        result = email_provider.send(context)
        
        assert result['success'] is True
        assert result['recipient'] == 'test@example.com'
        assert result['subject'] == 'Test Subject'

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_email_with_special_characters(self, mock_random, email_provider):
        """Test email sending with special characters in content."""
        context = {
            'to_email': 'test@example.com',
            'subject': 'Tést Sübject with 特殊字符',
            'body': 'Body with émojis 🎉 and spëcial chars'
        }
        
        result = email_provider.send(context)
        
        assert result['success'] is True
        assert result['subject'] == context['subject']

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_email_valid_email_formats(self, mock_random, email_provider):
        """Test email sending with various valid email formats."""
        valid_emails = [
            'simple@example.com',
            'user.name@example.com',
            'user+tag@example.co.uk',
            'user123@example-domain.com'
        ]
        
        for email in valid_emails:
            context = {
                'to_email': email,
                'subject': 'Test',
                'body': 'Test body'
            }
            
            result = email_provider.send(context)
            assert result['success'] is True
            assert result['recipient'] == email
