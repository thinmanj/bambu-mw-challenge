"""
Unit tests for the SMS adapter.
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.unit
class TestSMSProvider:
    """Test cases for SMSProvider."""

    def test_sms_provider_initialization(self, sms_adapter):
        """Test that SMSProvider initializes correctly."""
        assert sms_adapter is not None
        assert hasattr(sms_adapter, 'send')

    def test_send_sms_success(self, sms_adapter, sms_context):
        """Test successful SMS sending."""
        result = sms_adapter.send(sms_context)
        
        assert result is not None
        assert result['success'] is True
        assert result['provider'] == 'sms'
        assert result['recipient'] == sms_context['phone_number']
        assert result['message'] == sms_context['message']
        assert 'message_id' in result

    def test_send_sms_with_recipient_fallback(self, sms_adapter):
        """Test SMS sending with recipient field fallback."""
        context = {
            'recipient': '+1234567890',
            'message': 'Test SMS message'
        }
        
        result = sms_adapter.send(context)
        
        assert result['success'] is True
        assert result['recipient'] == '+1234567890'

    def test_send_sms_missing_phone_number(self, sms_adapter):
        """Test SMS sending fails when phone number is missing."""
        context = {
            'message': 'Test SMS message'
            # Missing phone_number and recipient
        }
        
        result = sms_adapter.send(context)
        
        assert result['success'] is False
        assert result['error'] == 'Missing recipient phone number'
        assert result['provider'] == 'sms'

    def test_send_sms_missing_message(self, sms_adapter):
        """Test SMS sending fails when message is missing."""
        context = {
            'phone_number': '+1234567890'
            # Missing message
        }
        
        result = sms_adapter.send(context)
        
        assert result['success'] is False
        assert result['error'] == 'Missing message content'
        assert result['provider'] == 'sms'

    def test_send_sms_with_body_fallback(self, sms_adapter):
        """Test SMS sending with body field fallback for message."""
        context = {
            'phone_number': '+1234567890',
            'body': 'Test SMS message via body field'
        }
        
        result = sms_adapter.send(context)
        
        assert result['success'] is True
        assert result['message'] == 'Test SMS message via body field'

    def test_send_sms_message_id_generation(self, sms_adapter, sms_context):
        """Test that message ID is generated consistently."""
        result1 = sms_adapter.send(sms_context)
        result2 = sms_adapter.send(sms_context)
        
        # Same context should generate same message ID
        assert result1['message_id'] == result2['message_id']

    def test_send_sms_different_contexts_different_ids(self, sms_adapter):
        """Test that different contexts generate different message IDs."""
        context1 = {
            'phone_number': '+1111111111',
            'message': 'Message 1'
        }
        context2 = {
            'phone_number': '+2222222222',
            'message': 'Message 2'
        }
        
        result1 = sms_adapter.send(context1)
        result2 = sms_adapter.send(context2)
        
        assert result1['message_id'] != result2['message_id']

    @patch('adapters.sms.logger')
    def test_send_sms_logging(self, mock_logger, sms_adapter, sms_context):
        """Test that SMS sending is properly logged."""
        sms_adapter.send(sms_context)
        
        # Check that info log was called
        mock_logger.info.assert_called()
        log_call_args = mock_logger.info.call_args[0][0]
        assert 'Sending SMS to' in log_call_args
        assert sms_context['phone_number'] in log_call_args

    @patch('adapters.sms.logger')
    def test_send_sms_error_logging(self, mock_logger, sms_adapter, invalid_sms_context):
        """Test that SMS errors are properly logged."""
        sms_adapter.send(invalid_sms_context)
        
        # Check that error log was called
        mock_logger.error.assert_called()
        log_call_args = mock_logger.error.call_args[0][0]
        assert 'SMS sending failed' in log_call_args

    def test_send_sms_long_message_logging(self, sms_adapter):
        """Test logging behavior with long SMS message."""
        long_message = "x" * 100  # Long message
        context = {
            'phone_number': '+1234567890',
            'message': long_message
        }
        
        with patch('adapters.sms.logger') as mock_logger:
            sms_adapter.send(context)
            
            # Check info log was called and message was truncated
            mock_logger.info.assert_called()
            log_call_args = mock_logger.info.call_args[0][0]
            assert '...' in log_call_args  # Should be truncated

    def test_send_sms_short_message_logging(self, sms_adapter):
        """Test logging behavior with short SMS message."""
        short_message = "Short SMS"
        context = {
            'phone_number': '+1234567890',
            'message': short_message
        }
        
        with patch('adapters.sms.logger') as mock_logger:
            sms_adapter.send(context)
            
            # Check info log was called and message not truncated
            mock_logger.info.assert_called()
            log_call_args = mock_logger.info.call_args[0][0]
            assert short_message in log_call_args  # Should not be truncated

    def test_send_sms_response_structure(self, sms_adapter, sms_context):
        """Test that SMS response has correct structure."""
        result = sms_adapter.send(sms_context)
        
        required_fields = ['success', 'message_id', 'provider', 'recipient', 'message']
        for field in required_fields:
            assert field in result

        # Check data types
        assert isinstance(result['success'], bool)
        assert isinstance(result['message_id'], str)
        assert isinstance(result['provider'], str)
        assert isinstance(result['recipient'], str)
        assert isinstance(result['message'], str)

    def test_send_sms_empty_message(self, sms_adapter):
        """Test SMS sending with empty message."""
        context = {
            'phone_number': '+1234567890',
            'message': ''
        }
        
        result = sms_adapter.send(context)
        
        assert result['success'] is False
        assert result['error'] == 'Missing message content'

    def test_send_sms_phone_number_validation(self, sms_adapter):
        """Test various phone number formats."""
        test_numbers = [
            '+1234567890',
            '1234567890', 
            '+44 123 456 7890',
            '(555) 123-4567'
        ]
        
        for number in test_numbers:
            context = {
                'phone_number': number,
                'message': 'Test message'
            }
            
            result = sms_adapter.send(context)
            assert result['success'] is True
            assert result['recipient'] == number
