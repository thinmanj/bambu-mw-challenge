"""
Comprehensive unit tests for SMS adapter.
"""

import pytest
from unittest.mock import patch, MagicMock
from adapters.sms import SMSProvider
from core.resilience.retry import RetryableError, NonRetryableError


@pytest.fixture
def sms_provider():
    """Create SMS provider for testing."""
    return SMSProvider()


@pytest.fixture
def valid_sms_context():
    """Valid SMS context for testing."""
    return {
        'phone_number': '+1234567890',
        'message': 'Test SMS message'
    }


@pytest.mark.unit
class TestSMSProvider:
    """Test cases for SMSProvider."""

    def test_sms_provider_initialization(self, sms_provider):
        """Test that SMSProvider initializes correctly."""
        assert sms_provider is not None
        assert hasattr(sms_provider, 'send')
        assert sms_provider.adapter_name == "sms"

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_sms_success(self, mock_random, sms_provider, valid_sms_context):
        """Test successful SMS sending."""
        result = sms_provider.send(valid_sms_context)
        
        assert result is not None
        assert result['success'] is True
        assert result['provider'] == 'sms'
        assert result['recipient'] == valid_sms_context['phone_number']
        assert result['message'] == valid_sms_context['message']
        assert 'message_id' in result
        assert result['message_id'].startswith('sms_msg_')

    @patch('random.random', return_value=0.5)  # No random failures  
    def test_send_sms_with_recipient_fallback(self, mock_random, sms_provider):
        """Test SMS sending with recipient field fallback."""
        context = {
            'recipient': '+1234567890',
            'message': 'Test SMS'
        }
        
        result = sms_provider.send(context)
        
        assert result['success'] is True
        assert result['recipient'] == '+1234567890'

    def test_send_sms_missing_recipient(self, sms_provider):
        """Test SMS sending fails when recipient is missing."""
        context = {
            'message': 'Test SMS'
            # Missing phone_number and recipient
        }
        
        with pytest.raises(NonRetryableError) as exc_info:
            sms_provider.send(context)
        
        assert "Missing recipient" in str(exc_info.value)

    def test_send_sms_missing_message(self, sms_provider):
        """Test SMS sending fails when message is missing."""
        context = {
            'phone_number': '+1234567890'
            # Missing message
        }
        
        with pytest.raises(NonRetryableError) as exc_info:
            sms_provider.send(context)
        
        assert "Missing message" in str(exc_info.value)

    def test_send_sms_invalid_phone_format(self, sms_provider):
        """Test SMS sending fails with invalid phone format."""
        invalid_phones = [
            'not-a-phone',  # Not numeric and doesn't start with +
            '123-456-7890-extra',  # Contains non-numeric characters, no +
        ]
        
        for phone in invalid_phones:
            context = {
                'phone_number': phone,
                'message': 'Test SMS'
            }
            
            with pytest.raises(Exception) as exc_info:  # Can be wrapped in RetryError
                sms_provider.send(context)
            
            assert "Invalid phone number format" in str(exc_info.value)

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_sms_valid_phone_formats(self, mock_random, sms_provider):
        """Test SMS sending with various valid phone formats."""
        valid_phones = [
            '+1234567890',
            '+12345678901',  # 11 digits
            '+123456789012'  # 12 digits
        ]
        
        for phone in valid_phones:
            context = {
                'phone_number': phone,
                'message': 'Test SMS'
            }
            
            result = sms_provider.send(context)
            assert result['success'] is True
            assert result['recipient'] == phone

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_sms_message_id_generation(self, mock_random, sms_provider, valid_sms_context):
        """Test that message ID is generated consistently."""
        result1 = sms_provider.send(valid_sms_context)
        result2 = sms_provider.send(valid_sms_context)
        
        # Same context should generate same message ID
        assert result1['message_id'] == result2['message_id']

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_sms_different_contexts_different_ids(self, mock_random, sms_provider):
        """Test that different contexts generate different message IDs."""
        context1 = {
            'phone_number': '+1234567890',
            'message': 'Message 1'
        }
        context2 = {
            'phone_number': '+1234567891',
            'message': 'Message 2'
        }
        
        result1 = sms_provider.send(context1)
        result2 = sms_provider.send(context2)
        
        assert result1['message_id'] != result2['message_id']

    @patch('random.random', return_value=0.5)  # No random failures
    @patch('adapters.sms.logger')
    def test_send_sms_logging(self, mock_logger, mock_random, sms_provider, valid_sms_context):
        """Test that SMS sending is properly logged."""
        sms_provider.send(valid_sms_context)
        
        # Check that info log was called
        mock_logger.info.assert_called()
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        
        # Should have sending logs (initialization happens before patch)
        assert any('Sending SMS to' in call for call in log_calls)

    @patch('random.random', return_value=0.05)  # Force retryable error
    def test_send_sms_retryable_error(self, mock_random, sms_provider, valid_sms_context):
        """Test that retryable errors are properly raised."""
        with pytest.raises(Exception) as exc_info:  # Could be RetryError or RetryableError
            sms_provider.send(valid_sms_context)
        
        # Check if it's a tenacity RetryError that wraps the original error
        exc_str = str(exc_info.value)
        if hasattr(exc_info.value, 'last_attempt') and hasattr(exc_info.value.last_attempt, 'exception'):
            exc_str = str(exc_info.value.last_attempt.exception())
        assert "SMS API rate limit exceeded" in exc_str

    @patch('random.random', return_value=0.10)  # Force non-retryable error (between 0.08 and 0.12)
    def test_send_sms_non_retryable_error(self, mock_random, sms_provider, valid_sms_context):
        """Test that non-retryable errors are properly raised."""
        with pytest.raises(Exception) as exc_info:  # Could be RetryError wrapping NonRetryableError
            sms_provider.send(valid_sms_context)
        
        # Check if it's a tenacity RetryError that wraps the original error
        exc_str = str(exc_info.value)
        if hasattr(exc_info.value, 'last_attempt') and hasattr(exc_info.value.last_attempt, 'exception'):
            exc_str = str(exc_info.value.last_attempt.exception())
        assert "Phone number is blocked or invalid" in exc_str

    def test_send_sms_invalid_context_type(self, sms_provider):
        """Test SMS sending fails with invalid context type."""
        with pytest.raises(NonRetryableError) as exc_info:
            sms_provider.send("invalid_context")
        
        assert "Invalid context" in str(exc_info.value)

    def test_send_sms_empty_context(self, sms_provider):
        """Test SMS sending fails with empty context."""
        with pytest.raises(NonRetryableError) as exc_info:
            sms_provider.send({})
        
        assert "Missing recipient" in str(exc_info.value)

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_sms_response_structure(self, mock_random, sms_provider, valid_sms_context):
        """Test that SMS response has correct structure."""
        result = sms_provider.send(valid_sms_context)
        
        required_fields = ['success', 'message_id', 'provider', 'recipient', 'message']
        for field in required_fields:
            assert field in result

        # Check data types
        assert isinstance(result['success'], bool)
        assert isinstance(result['message_id'], str)
        assert isinstance(result['provider'], str)
        assert isinstance(result['recipient'], str)
        assert isinstance(result['message'], str)

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_sms_with_special_characters(self, mock_random, sms_provider):
        """Test SMS sending with special characters in message."""
        context = {
            'phone_number': '+1234567890',
            'message': 'SMS with émojis 🎉 and spëcial chars 特殊字符'
        }
        
        result = sms_provider.send(context)
        
        assert result['success'] is True
        assert result['message'] == context['message']

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_sms_long_message(self, mock_random, sms_provider):
        """Test SMS sending with long message."""
        long_message = "x" * 500  # Very long message
        context = {
            'phone_number': '+1234567890',
            'message': long_message
        }
        
        result = sms_provider.send(context)
        
        assert result['success'] is True
        assert result['message'] == long_message

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_sms_empty_message(self, mock_random, sms_provider):
        """Test SMS sending fails with empty message."""
        context = {
            'phone_number': '+1234567890',
            'message': ''  # Empty message
        }
        
        with pytest.raises(NonRetryableError) as exc_info:
            sms_provider.send(context)
        
        assert "Missing message" in str(exc_info.value)

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_sms_whitespace_only_message(self, mock_random, sms_provider):
        """Test SMS sending succeeds with whitespace-only message."""
        context = {
            'phone_number': '+1234567890',
            'message': '   '  # Only whitespace
        }
        
        result = sms_provider.send(context)
        
        assert result['success'] is True
        assert result['message'] == '   '  # Preserves whitespace

    @patch('random.random', return_value=0.5)  # No random failures  
    def test_send_sms_with_body_fallback(self, mock_random, sms_provider):
        """Test SMS sending with body field as message fallback."""
        context = {
            'phone_number': '+1234567890',
            'body': 'Test SMS from body field'  # Using body instead of message
        }
        
        result = sms_provider.send(context)
        
        assert result['success'] is True
        assert result['recipient'] == '+1234567890'
        assert result['message'] == 'Test SMS from body field'
