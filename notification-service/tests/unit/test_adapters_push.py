"""
Unit tests for the push notification adapter.
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestPushProvider:
    """Test cases for PushProvider."""

    def test_push_provider_initialization(self, push_adapter):
        """Test that PushProvider initializes correctly."""
        assert push_adapter is not None
        assert hasattr(push_adapter, 'send')

    def test_send_push_success(self, push_adapter, push_context):
        """Test successful push notification sending."""
        result = push_adapter.send(push_context)
        
        assert result is not None
        assert result['success'] is True
        assert result['provider'] == 'push'
        assert result['recipient'] == push_context['device_token']
        assert result['title'] == push_context['title']
        assert result['message'] == push_context['message']
        assert 'message_id' in result

    def test_send_push_with_recipient_fallback(self, push_adapter):
        """Test push sending with recipient field fallback."""
        context = {
            'recipient': 'device_token_123',
            'title': 'Test Push',
            'message': 'Test push message'
        }
        
        result = push_adapter.send(context)
        
        assert result['success'] is True
        assert result['recipient'] == 'device_token_123'

    def test_send_push_missing_device_token(self, push_adapter):
        """Test push sending fails when device token is missing."""
        context = {
            'title': 'Test Push',
            'message': 'Test push message'
            # Missing device_token and recipient
        }
        
        result = push_adapter.send(context)
        
        assert result['success'] is False
        assert result['error'] == 'Missing recipient device token'
        assert result['provider'] == 'push'

    def test_send_push_missing_message(self, push_adapter):
        """Test push sending fails when message is missing."""
        context = {
            'device_token': 'device_token_123',
            'title': 'Test Push'
            # Missing message
        }
        
        result = push_adapter.send(context)
        
        assert result['success'] is False
        assert result['error'] == 'Missing message content'
        assert result['provider'] == 'push'

    def test_send_push_with_body_fallback(self, push_adapter):
        """Test push sending with body field fallback for message."""
        context = {
            'device_token': 'device_token_123',
            'title': 'Test Push',
            'body': 'Test push message via body field'
        }
        
        result = push_adapter.send(context)
        
        assert result['success'] is True
        assert result['message'] == 'Test push message via body field'

    def test_send_push_with_default_title(self, push_adapter):
        """Test push sending with default title."""
        context = {
            'device_token': 'device_token_123',
            'message': 'Test push message'
            # Missing title - should use default
        }
        
        result = push_adapter.send(context)
        
        assert result['success'] is True
        assert result['title'] == 'Notification'

    def test_send_push_message_id_generation(self, push_adapter, push_context):
        """Test that message ID is generated consistently."""
        result1 = push_adapter.send(push_context)
        result2 = push_adapter.send(push_context)
        
        # Same context should generate same message ID
        assert result1['message_id'] == result2['message_id']

    def test_send_push_different_contexts_different_ids(self, push_adapter):
        """Test that different contexts generate different message IDs."""
        context1 = {
            'device_token': 'token1',
            'title': 'Title 1',
            'message': 'Message 1'
        }
        context2 = {
            'device_token': 'token2',
            'title': 'Title 2',
            'message': 'Message 2'
        }
        
        result1 = push_adapter.send(context1)
        result2 = push_adapter.send(context2)
        
        assert result1['message_id'] != result2['message_id']

    @patch('adapters.push.logger')
    def test_send_push_logging(self, mock_logger, push_adapter, push_context):
        """Test that push notification sending is properly logged."""
        push_adapter.send(push_context)
        
        # Check that info log was called
        mock_logger.info.assert_called()
        log_call_args = mock_logger.info.call_args[0][0]
        assert 'Sending push to' in log_call_args
        # Device token should be truncated for security
        assert push_context['device_token'][:20] in log_call_args

    @patch('adapters.push.logger')
    def test_send_push_error_logging(self, mock_logger, push_adapter, invalid_push_context):
        """Test that push errors are properly logged."""
        push_adapter.send(invalid_push_context)
        
        # Check that error log was called
        mock_logger.error.assert_called()
        log_call_args = mock_logger.error.call_args[0][0]
        assert 'Push notification failed' in log_call_args

    def test_send_push_long_message_logging(self, push_adapter):
        """Test logging behavior with long push message."""
        long_message = "x" * 200  # Long message
        context = {
            'device_token': 'device_token_123',
            'title': 'Test',
            'message': long_message
        }
        
        with patch('adapters.push.logger') as mock_logger:
            push_adapter.send(context)
            
            # Check debug log was called and message was truncated
            mock_logger.debug.assert_called()
            log_call_args = mock_logger.debug.call_args[0][0]
            assert '...' in log_call_args  # Should be truncated

    def test_send_push_short_message_logging(self, push_adapter):
        """Test logging behavior with short push message."""
        short_message = "Short push"
        context = {
            'device_token': 'device_token_123',
            'title': 'Test',
            'message': short_message
        }
        
        with patch('adapters.push.logger') as mock_logger:
            push_adapter.send(context)
            
            # Check debug log was called and message not truncated
            mock_logger.debug.assert_called()
            log_call_args = mock_logger.debug.call_args[0][0]
            assert short_message in log_call_args  # Should not be truncated

    def test_send_push_device_token_masking(self, push_adapter):
        """Test that long device tokens are masked in logs."""
        long_token = "a" * 50  # Long device token
        context = {
            'device_token': long_token,
            'title': 'Test',
            'message': 'Test message'
        }
        
        with patch('adapters.push.logger') as mock_logger:
            push_adapter.send(context)
            
            # Check info log was called and token was truncated
            mock_logger.info.assert_called()
            log_call_args = mock_logger.info.call_args[0][0]
            assert long_token[:20] in log_call_args  # Only first 20 chars
            assert '...' in log_call_args  # Should show truncation

    def test_send_push_short_device_token_not_masked(self, push_adapter):
        """Test that short device tokens are not masked in logs."""
        short_token = "short_token"
        context = {
            'device_token': short_token,
            'title': 'Test',
            'message': 'Test message'
        }
        
        with patch('adapters.push.logger') as mock_logger:
            push_adapter.send(context)
            
            # Check info log was called and token not truncated
            mock_logger.info.assert_called()
            log_call_args = mock_logger.info.call_args[0][0]
            assert short_token in log_call_args  # Should not be truncated

    def test_send_push_response_structure(self, push_adapter, push_context):
        """Test that push response has correct structure."""
        result = push_adapter.send(push_context)
        
        required_fields = ['success', 'message_id', 'provider', 'recipient', 'title', 'message']
        for field in required_fields:
            assert field in result

        # Check data types
        assert isinstance(result['success'], bool)
        assert isinstance(result['message_id'], str)
        assert isinstance(result['provider'], str)
        assert isinstance(result['recipient'], str)
        assert isinstance(result['title'], str)
        assert isinstance(result['message'], str)

    def test_send_push_empty_message(self, push_adapter):
        """Test push sending with empty message."""
        context = {
            'device_token': 'device_token_123',
            'title': 'Test',
            'message': ''
        }
        
        result = push_adapter.send(context)
        
        assert result['success'] is False
        assert result['error'] == 'Missing message content'

    def test_send_push_various_device_tokens(self, push_adapter):
        """Test various device token formats."""
        test_tokens = [
            'simple_token',
            'token-with-dashes',
            'token_with_underscores',
            'VeryLongTokenWithMixedCaseAndNumbers123456789',
            '12345'
        ]
        
        for token in test_tokens:
            context = {
                'device_token': token,
                'title': 'Test',
                'message': 'Test message'
            }
            
            result = push_adapter.send(context)
            assert result['success'] is True
            assert result['recipient'] == token
