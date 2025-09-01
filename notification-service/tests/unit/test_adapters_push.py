"""
Comprehensive unit tests for push adapter.
"""

import pytest
from unittest.mock import patch, MagicMock
from adapters.push import PushProvider
from core.resilience.retry import RetryableError, NonRetryableError
import tenacity


@pytest.fixture
def push_provider():
    """Create push provider for testing."""
    return PushProvider()


@pytest.fixture
def valid_push_context():
    """Valid push context for testing."""
    return {
        'device_token': 'abc123device456token789',
        'title': 'Test Push Title',
        'body': 'Test push notification body'
    }


@pytest.mark.unit
class TestPushProvider:
    """Test cases for PushProvider."""

    def test_push_provider_initialization(self, push_provider):
        """Test that PushProvider initializes correctly."""
        assert push_provider is not None
        assert hasattr(push_provider, 'send')
        assert push_provider.adapter_name == "push"

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_push_success(self, mock_random, push_provider, valid_push_context):
        """Test successful push notification sending."""
        result = push_provider.send(valid_push_context)
        
        assert result is not None
        assert result['success'] is True
        assert result['provider'] == 'push'
        assert result['recipient'] == valid_push_context['device_token']
        assert result['title'] == valid_push_context['title']
        assert result['body'] == valid_push_context['body']
        assert 'message_id' in result
        assert result['message_id'].startswith('push_msg_')

    @patch('random.random', return_value=0.5)  # No random failures  
    def test_send_push_with_recipient_fallback(self, mock_random, push_provider):
        """Test push sending with recipient field fallback."""
        context = {
            'recipient': 'device_token_123',
            'title': 'Test Title',
            'body': 'Test body'
        }
        
        result = push_provider.send(context)
        
        assert result['success'] is True
        assert result['recipient'] == 'device_token_123'

    def test_send_push_missing_device_token(self, push_provider):
        """Test push sending fails when device token is missing."""
        context = {
            'title': 'Test Title',
            'body': 'Test body'
            # Missing device_token and recipient
        }
        
        with pytest.raises(NonRetryableError) as exc_info:
            push_provider.send(context)
        
        assert "Missing recipient" in str(exc_info.value)

    def test_send_push_missing_title_and_body(self, push_provider):
        """Test push sending fails when both title and body are missing."""
        context = {
            'device_token': 'abc123device456token789'
            # Missing title, body, and message
        }
        
        with pytest.raises(NonRetryableError) as exc_info:
            push_provider.send(context)
        
        assert "Missing message" in str(exc_info.value)

    def test_send_push_with_title_only(self, push_provider):
        """Test push sending fails with title only (no body/message)."""
        context = {
            'device_token': 'abc123device456token789',
            'title': 'Test Title'
            # Missing body/message - should fail validation
        }
        
        with pytest.raises(NonRetryableError) as exc_info:
            push_provider.send(context)
        
        assert "Missing message" in str(exc_info.value)

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_push_with_body_only(self, mock_random, push_provider):
        """Test push sending with body only (no title)."""
        context = {
            'device_token': 'abc123device456token789',
            'body': 'Test body content'
            # Missing title
        }
        
        result = push_provider.send(context)
        
        assert result['success'] is True
        assert result['title'] == 'Notification'  # Should use default
        assert result['body'] == 'Test body content'

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_push_with_message_fallback(self, mock_random, push_provider):
        """Test push sending with message field as body fallback."""
        context = {
            'device_token': 'abc123device456token789',
            'title': 'Test Title',
            'message': 'Test message as body'  # Using message instead of body
        }
        
        result = push_provider.send(context)
        
        assert result['success'] is True
        assert result['title'] == 'Test Title'
        assert result['body'] == 'Test message as body'

    def test_send_push_invalid_device_token(self, push_provider):
        """Test push sending fails with invalid device token."""
        invalid_tokens = [
            '',  # Empty token
            '   ',  # Whitespace only
            'abc',  # Too short
        ]
        
        for token in invalid_tokens:
            context = {
                'device_token': token,
                'title': 'Test Title',
                'body': 'Test body'
            }
            
            with pytest.raises(Exception) as exc_info:  # Can be wrapped in RetryError
                push_provider.send(context)
            
            assert "Device token too short" in str(exc_info.value)

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_push_valid_device_tokens(self, mock_random, push_provider):
        """Test push sending with various valid device token formats."""
        valid_tokens = [
            'abc123def456',  # Short alphanumeric
            'ABCDEF1234567890abcdef',  # Mixed case
            '1234567890abcdef1234567890abcdef12345678',  # Longer hex-like
            'device_token_with_underscores_123'  # With underscores
        ]
        
        for token in valid_tokens:
            context = {
                'device_token': token,
                'title': 'Test Title',
                'body': 'Test body'
            }
            
            result = push_provider.send(context)
            assert result['success'] is True
            assert result['recipient'] == token

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_push_message_id_generation(self, mock_random, push_provider, valid_push_context):
        """Test that message ID is generated consistently."""
        result1 = push_provider.send(valid_push_context)
        result2 = push_provider.send(valid_push_context)
        
        # Same context should generate same message ID
        assert result1['message_id'] == result2['message_id']

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_push_different_contexts_different_ids(self, mock_random, push_provider):
        """Test that different contexts generate different message IDs."""
        context1 = {
            'device_token': 'device_token_123456789',
            'title': 'Title 1',
            'body': 'Body 1'
        }
        context2 = {
            'device_token': 'device_token_987654321',
            'title': 'Title 2',
            'body': 'Body 2'
        }
        
        result1 = push_provider.send(context1)
        result2 = push_provider.send(context2)
        
        assert result1['message_id'] != result2['message_id']

    @patch('random.random', return_value=0.5)  # No random failures
    @patch('adapters.push.logger')
    def test_send_push_logging(self, mock_logger, mock_random, push_provider, valid_push_context):
        """Test that push sending is properly logged."""
        push_provider.send(valid_push_context)
        
        # Check that info log was called for sending
        mock_logger.info.assert_called()
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        
        # Should have sending logs (initialization happens before patch)
        assert any('Sending push to' in call for call in log_calls)

    @patch('random.random', return_value=0.05)  # Force retryable error
    def test_send_push_retryable_error(self, mock_random, push_provider, valid_push_context):
        """Test that retryable errors are properly raised."""
        with pytest.raises(Exception) as exc_info:  # Could be RetryError or RetryableError
            push_provider.send(valid_push_context)
        
        # Check if it's a tenacity RetryError that wraps the original error
        exc_str = str(exc_info.value)
        if hasattr(exc_info.value, 'last_attempt') and hasattr(exc_info.value.last_attempt, 'exception'):
            exc_str = str(exc_info.value.last_attempt.exception())
        assert "FCM server temporarily unavailable" in exc_str

    @patch('random.random', return_value=0.095)  # Force non-retryable error (between 0.09 and 0.13)
    def test_send_push_non_retryable_error(self, mock_random, push_provider, valid_push_context):
        """Test that non-retryable errors are properly raised."""
        with pytest.raises(Exception) as exc_info:  # Could be RetryError wrapping NonRetryableError
            push_provider.send(valid_push_context)
        
        # Check if it's a tenacity RetryError that wraps the original error
        exc_str = str(exc_info.value)
        if hasattr(exc_info.value, 'last_attempt') and hasattr(exc_info.value.last_attempt, 'exception'):
            exc_str = str(exc_info.value.last_attempt.exception())
        assert "Device token is invalid or unregistered" in exc_str

    def test_send_push_invalid_context_type(self, push_provider):
        """Test push sending fails with invalid context type."""
        with pytest.raises(NonRetryableError) as exc_info:
            push_provider.send("invalid_context")
        
        assert "Invalid context" in str(exc_info.value)

    def test_send_push_empty_context(self, push_provider):
        """Test push sending fails with empty context."""
        with pytest.raises(NonRetryableError) as exc_info:
            push_provider.send({})
        
        assert "Missing recipient" in str(exc_info.value)

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_push_response_structure(self, mock_random, push_provider, valid_push_context):
        """Test that push response has correct structure."""
        result = push_provider.send(valid_push_context)
        
        required_fields = ['success', 'message_id', 'provider', 'recipient', 'title', 'body']
        for field in required_fields:
            assert field in result

        # Check data types
        assert isinstance(result['success'], bool)
        assert isinstance(result['message_id'], str)
        assert isinstance(result['provider'], str)
        assert isinstance(result['recipient'], str)
        assert isinstance(result['title'], str)
        assert isinstance(result['body'], str)

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_push_with_special_characters(self, mock_random, push_provider):
        """Test push sending with special characters in content."""
        context = {
            'device_token': 'abc123device456token789',
            'title': 'Tést Tïfle with 特殊字符',
            'body': 'Push with émojis 🎉 and spëcial chars'
        }
        
        result = push_provider.send(context)
        
        assert result['success'] is True
        assert result['title'] == context['title']
        assert result['body'] == context['body']

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_push_long_content(self, mock_random, push_provider):
        """Test push sending with long title and body."""
        long_title = "x" * 100  # Long title
        long_body = "y" * 500   # Long body
        context = {
            'device_token': 'abc123device456token789',
            'title': long_title,
            'body': long_body
        }
        
        result = push_provider.send(context)
        
        assert result['success'] is True
        assert result['title'] == long_title
        assert result['body'] == long_body

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_push_empty_title_and_body(self, mock_random, push_provider):
        """Test push sending fails with empty title and body."""
        context = {
            'device_token': 'abc123device456token789',
            'title': '',
            'body': ''
        }
        
        with pytest.raises(NonRetryableError) as exc_info:
            push_provider.send(context)
        
        assert "Missing message" in str(exc_info.value)

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_push_whitespace_only_content(self, mock_random, push_provider):
        """Test push sending succeeds with whitespace-only content."""
        context = {
            'device_token': 'abc123device456token789',
            'title': '   ',  # Only whitespace
            'body': '   '    # Only whitespace
        }
        
        result = push_provider.send(context)
        
        assert result['success'] is True
        assert result['title'] == '   '  # Preserves whitespace
        assert result['body'] == '   '  # Preserves whitespace

    @patch('random.random', return_value=0.5)  # No random failures
    def test_send_push_with_additional_data(self, mock_random, push_provider):
        """Test push sending with additional data fields."""
        context = {
            'device_token': 'abc123device456token789',
            'title': 'Test Title',
            'body': 'Test body',
            'additional_field': 'Should be ignored'  # Extra fields should not cause issues
        }
        
        result = push_provider.send(context)
        
        assert result['success'] is True
        assert 'additional_field' not in result  # Should not be included in response
