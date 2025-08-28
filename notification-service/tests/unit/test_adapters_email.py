"""
Unit tests for the email adapter.
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestEmailProvider:
    """Test cases for EmailProvider."""

    def test_email_provider_initialization(self, email_adapter):
        """Test that EmailProvider initializes correctly."""
        assert email_adapter is not None
        assert hasattr(email_adapter, 'send')

    def test_send_email_success(self, email_adapter, email_context):
        """Test successful email sending."""
        result = email_adapter.send(email_context)
        
        assert result is not None
        assert result['success'] is True
        assert result['provider'] == 'email'
        assert result['recipient'] == email_context['to_email']
        assert result['subject'] == email_context['subject']
        assert 'message_id' in result

    def test_send_email_with_recipient_fallback(self, email_adapter):
        """Test email sending with recipient field fallback."""
        context = {
            'recipient': 'test@example.com',
            'subject': 'Test Subject',
            'body': 'Test body'
        }
        
        result = email_adapter.send(context)
        
        assert result['success'] is True
        assert result['recipient'] == 'test@example.com'

    def test_send_email_missing_recipient(self, email_adapter):
        """Test email sending fails when recipient is missing."""
        context = {
            'subject': 'Test Subject',
            'body': 'Test body'
            # Missing to_email and recipient
        }
        
        result = email_adapter.send(context)
        
        assert result['success'] is False
        assert result['error'] == 'Missing recipient email address'
        assert result['provider'] == 'email'

    def test_send_email_with_default_values(self, email_adapter):
        """Test email sending with default values."""
        context = {
            'to_email': 'test@example.com'
            # Missing subject and body - should use defaults
        }
        
        result = email_adapter.send(context)
        
        assert result['success'] is True
        assert result['subject'] == 'No Subject'

    def test_send_email_message_id_generation(self, email_adapter, email_context):
        """Test that message ID is generated consistently."""
        result1 = email_adapter.send(email_context)
        result2 = email_adapter.send(email_context)
        
        # Same context should generate same message ID
        assert result1['message_id'] == result2['message_id']

    def test_send_email_different_contexts_different_ids(self, email_adapter):
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
        
        result1 = email_adapter.send(context1)
        result2 = email_adapter.send(context2)
        
        assert result1['message_id'] != result2['message_id']

    @patch('adapters.email.logger')
    def test_send_email_logging(self, mock_logger, email_adapter, email_context):
        """Test that email sending is properly logged."""
        email_adapter.send(email_context)
        
        # Check that info log was called
        mock_logger.info.assert_called()
        log_call_args = mock_logger.info.call_args[0][0]
        assert 'Sending email to' in log_call_args
        assert email_context['to_email'] in log_call_args

    @patch('adapters.email.logger')
    def test_send_email_error_logging(self, mock_logger, email_adapter, invalid_email_context):
        """Test that email errors are properly logged."""
        email_adapter.send(invalid_email_context)
        
        # Check that error log was called
        mock_logger.error.assert_called()
        log_call_args = mock_logger.error.call_args[0][0]
        assert 'Email sending failed' in log_call_args

    def test_send_email_long_body_logging(self, email_adapter):
        """Test logging behavior with long email body."""
        long_body = "x" * 200  # Long body
        context = {
            'to_email': 'test@example.com',
            'subject': 'Test',
            'body': long_body
        }
        
        with patch('adapters.email.logger') as mock_logger:
            email_adapter.send(context)
            
            # Check debug log was called for body
            mock_logger.debug.assert_called()
            log_call_args = mock_logger.debug.call_args[0][0]
            assert '...' in log_call_args  # Should be truncated

    def test_send_email_short_body_logging(self, email_adapter):
        """Test logging behavior with short email body."""
        short_body = "Short body"
        context = {
            'to_email': 'test@example.com',
            'subject': 'Test',
            'body': short_body
        }
        
        with patch('adapters.email.logger') as mock_logger:
            email_adapter.send(context)
            
            # Check debug log was called for body
            mock_logger.debug.assert_called()
            log_call_args = mock_logger.debug.call_args[0][0]
            assert short_body in log_call_args  # Should not be truncated

    def test_send_email_response_structure(self, email_adapter, email_context):
        """Test that email response has correct structure."""
        result = email_adapter.send(email_context)
        
        required_fields = ['success', 'message_id', 'provider', 'recipient', 'subject']
        for field in required_fields:
            assert field in result

        # Check data types
        assert isinstance(result['success'], bool)
        assert isinstance(result['message_id'], str)
        assert isinstance(result['provider'], str)
        assert isinstance(result['recipient'], str)
        assert isinstance(result['subject'], str)
