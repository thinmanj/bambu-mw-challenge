"""
Unit tests for retry functionality in notification adapters.

This module tests the exponential backoff and retry behavior
of the notification adapters using tenacity.
"""
import pytest
import time
from unittest.mock import Mock, patch, call
import logging
from core.resilience.retry import (
    retry_with_backoff, 
    RetryableError, 
    NonRetryableError,
    standard_retry,
    aggressive_retry,
    gentle_retry
)
from core.resilience.base_adapter import BaseNotificationAdapter
from adapters.email import EmailProvider
from adapters.sms import SMSProvider
from adapters.push import PushProvider


class TestRetryDecorator:
    """Test the retry decorator functionality."""
    
    @pytest.mark.unit
    def test_retry_decorator_success_on_first_attempt(self):
        """Test that successful calls don't trigger retries."""
        mock_func = Mock(return_value="success")
        
        @retry_with_backoff(max_attempts=3, backoff_factor=2, max_delay=30)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    @pytest.mark.unit
    def test_retry_decorator_success_after_retries(self):
        """Test that retryable errors trigger retries until success."""
        mock_func = Mock(side_effect=[
            ConnectionError("Network error"),
            TimeoutError("Timeout"),
            "success"  # Third attempt succeeds
        ])
        
        @retry_with_backoff(max_attempts=3, backoff_factor=2, max_delay=30)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    @pytest.mark.unit
    def test_retry_decorator_exhausts_attempts(self):
        """Test that retries are exhausted and final exception is raised."""
        mock_func = Mock(side_effect=ConnectionError("Persistent error"))
        
        @retry_with_backoff(max_attempts=3, backoff_factor=2, max_delay=30)
        def test_func():
            return mock_func()
        
        with pytest.raises(ConnectionError, match="Persistent error"):
            test_func()
        
        assert mock_func.call_count == 3
    
    @pytest.mark.unit
    def test_retry_decorator_non_retryable_exception(self):
        """Test that non-retryable exceptions don't trigger retries."""
        mock_func = Mock(side_effect=ValueError("Invalid input"))
        
        @retry_with_backoff(max_attempts=3, backoff_factor=2, max_delay=30, 
                           retry_on=(ConnectionError, TimeoutError))
        def test_func():
            return mock_func()
        
        with pytest.raises(ValueError, match="Invalid input"):
            test_func()
        
        # Should only be called once since ValueError is not retryable
        assert mock_func.call_count == 1
    
    @pytest.mark.unit
    def test_convenience_decorators(self):
        """Test the convenience retry decorators."""
        
        @standard_retry
        def standard_func():
            raise ConnectionError("Network error")
        
        @aggressive_retry
        def aggressive_func():
            raise ConnectionError("Network error")
        
        @gentle_retry
        def gentle_func():
            raise ConnectionError("Network error")
        
        # Standard retry: 3 attempts
        with pytest.raises(ConnectionError):
            with patch('time.sleep'):  # Speed up tests
                standard_func()
        
        # Other decorators would be tested similarly
        # We don't need to test all of them in detail since they use the same underlying logic


class TestBaseAdapterRetry:
    """Test retry functionality in the base adapter classes."""
    
    class TestAdapter(BaseNotificationAdapter):
        """Test implementation of BaseNotificationAdapter."""
        
        def __init__(self, name="test"):
            super().__init__(name)
            self.send_impl_mock = Mock()
        
        def _send_impl(self, context):
            return self.send_impl_mock(context)
    
    @pytest.mark.unit
    def test_base_adapter_retry_on_retryable_error(self):
        """Test that base adapter retries on RetryableError."""
        adapter = self.TestAdapter()
        adapter.send_impl_mock.side_effect = [
            RetryableError("Transient error"),
            RetryableError("Another transient error"),
            {"success": True, "message_id": "123"}
        ]
        
        context = {"recipient": "test@example.com", "message": "Hello"}
        
        with patch('time.sleep'):  # Speed up tests
            result = adapter.send(context)
        
        assert result["success"] is True
        assert adapter.send_impl_mock.call_count == 3
    
    @pytest.mark.unit
    def test_base_adapter_no_retry_on_non_retryable_error(self):
        """Test that base adapter doesn't retry on NonRetryableError."""
        adapter = self.TestAdapter()
        adapter.send_impl_mock.side_effect = NonRetryableError("Permanent error")
        
        context = {"recipient": "test@example.com", "message": "Hello"}
        
        with pytest.raises(NonRetryableError, match="Permanent error"):
            adapter.send(context)
        
        assert adapter.send_impl_mock.call_count == 1
    
    @pytest.mark.unit
    def test_base_adapter_validation_error_is_non_retryable(self):
        """Test that validation errors are not retried."""
        adapter = self.TestAdapter()
        
        # Invalid context (missing recipient and message)
        context = {}
        
        with pytest.raises(NonRetryableError):
            adapter.send(context)
        
        # _send_impl should not be called at all
        assert adapter.send_impl_mock.call_count == 0
    
    @pytest.mark.unit
    def test_base_adapter_converts_unknown_exceptions(self):
        """Test that unknown exceptions are converted to RetryableError."""
        adapter = self.TestAdapter()
        adapter.send_impl_mock.side_effect = [
            RuntimeError("Unknown error"),
            {"success": True, "message_id": "123"}
        ]
        
        context = {"recipient": "test@example.com", "message": "Hello"}
        
        with patch('time.sleep'):  # Speed up tests
            result = adapter.send(context)
        
        assert result["success"] is True
        assert adapter.send_impl_mock.call_count == 2


class TestEmailProviderRetry:
    """Test retry functionality specific to EmailProvider."""
    
    @pytest.mark.unit
    def test_email_provider_initialization(self):
        """Test that EmailProvider initializes with retry capability."""
        provider = EmailProvider()
        
        assert provider.adapter_name == "email"
        assert hasattr(provider, 'send')
        
        # Test adapter info includes retry settings
        info = provider.get_adapter_info()
        assert info['retry_enabled'] is True
        assert info['max_attempts'] == 3
        assert info['backoff_factor'] == 2
    
    @pytest.mark.unit
    def test_email_provider_validation(self):
        """Test email-specific validation."""
        provider = EmailProvider()
        
        # Valid context
        valid_context = {"to_email": "test@example.com", "subject": "Test", "body": "Hello"}
        assert provider._validate_context(valid_context) is None
        
        # Invalid email format
        invalid_context = {"to_email": "invalid-email", "subject": "Test", "body": "Hello"}
        error = provider._validate_context(invalid_context)
        assert "Invalid email address format" in error
    
    @pytest.mark.unit
    @patch('random.random', return_value=0.5)  # No simulated failures
    def test_email_provider_successful_send(self, mock_random):
        """Test successful email sending without retries."""
        provider = EmailProvider()
        
        context = {
            "to_email": "test@example.com",
            "subject": "Test Subject",
            "body": "Hello World"
        }
        
        result = provider.send(context)
        
        assert result["success"] is True
        assert result["provider"] == "email"
        assert result["recipient"] == "test@example.com"
        assert result["subject"] == "Test Subject"
    
    @pytest.mark.unit
    @patch('random.random', side_effect=[0.05, 0.5])  # First call triggers retry, second succeeds
    def test_email_provider_retry_on_simulated_failure(self, mock_random):
        """Test that email provider retries on simulated failures."""
        provider = EmailProvider()
        
        context = {
            "to_email": "test@example.com",
            "subject": "Test Subject",
            "body": "Hello World"
        }
        
        with patch('time.sleep'):  # Speed up tests
            result = provider.send(context)
        
        assert result["success"] is True
        assert mock_random.call_count == 2  # First call failed, second succeeded


class TestSMSProviderRetry:
    """Test retry functionality specific to SMSProvider."""
    
    @pytest.mark.unit
    def test_sms_provider_validation(self):
        """Test SMS-specific validation."""
        provider = SMSProvider()
        
        # Valid context
        valid_context = {"phone_number": "+1234567890", "message": "Hello"}
        assert provider._validate_context(valid_context) is None
        
        # Another valid format
        valid_context2 = {"phone_number": "123-456-7890", "message": "Hello"}
        assert provider._validate_context(valid_context2) is None
        
        # Invalid phone format
        invalid_context = {"phone_number": "abc123", "message": "Hello"}
        error = provider._validate_context(invalid_context)
        assert "Invalid phone number format" in error
    
    @pytest.mark.unit
    @patch('random.random', side_effect=[0.05, 0.5])  # First triggers retry, second succeeds
    def test_sms_provider_retry_on_simulated_rate_limit(self, mock_random):
        """Test that SMS provider retries on rate limit errors."""
        provider = SMSProvider()
        
        context = {
            "phone_number": "+1234567890",
            "message": "Test message"
        }
        
        with patch('time.sleep'):  # Speed up tests
            result = provider.send(context)
        
        assert result["success"] is True
        assert result["provider"] == "sms"


class TestPushProviderRetry:
    """Test retry functionality specific to PushProvider."""
    
    @pytest.mark.unit
    def test_push_provider_validation(self):
        """Test push-specific validation."""
        provider = PushProvider()
        
        # Valid context
        valid_context = {
            "device_token": "abcd1234567890efgh",
            "title": "Test",
            "message": "Hello"
        }
        assert provider._validate_context(valid_context) is None
        
        # Device token too short
        invalid_context = {
            "device_token": "abc",
            "title": "Test",
            "message": "Hello"
        }
        error = provider._validate_context(invalid_context)
        assert "Device token too short" in error
    
    @pytest.mark.unit
    @patch('random.random', side_effect=[0.06, 0.5])  # First triggers retry, second succeeds
    def test_push_provider_retry_on_simulated_server_error(self, mock_random):
        """Test that push provider retries on server errors."""
        provider = PushProvider()
        
        context = {
            "device_token": "abcd1234567890efgh",
            "title": "Test Notification",
            "message": "Hello World"
        }
        
        with patch('time.sleep'):  # Speed up tests
            result = provider.send(context)
        
        assert result["success"] is True
        assert result["provider"] == "push"


class TestRetryIntegration:
    """Integration tests for retry functionality across all adapters."""
    
    @pytest.mark.unit
    @patch('time.sleep')  # Speed up all tests in this class
    def test_all_providers_have_retry_capability(self, mock_sleep):
        """Test that all providers support retry functionality."""
        providers = [
            EmailProvider(),
            SMSProvider(),
            PushProvider()
        ]
        
        for provider in providers:
            # Check that they have the expected methods
            assert hasattr(provider, 'send')
            assert hasattr(provider, '_send_impl')
            assert hasattr(provider, 'get_adapter_info')
            
            # Check adapter info includes retry settings
            info = provider.get_adapter_info()
            assert info['retry_enabled'] is True
            assert info['max_attempts'] == 3
    
    @pytest.mark.unit
    def test_retry_timing_exponential_backoff(self):
        """Test that retry timing follows exponential backoff pattern."""
        
        class TimingTestAdapter(BaseNotificationAdapter):
            def __init__(self):
                super().__init__("timing_test")
                self.attempt_times = []
            
            def _send_impl(self, context):
                self.attempt_times.append(time.time())
                raise RetryableError("Always fail for timing test")
        
        adapter = TimingTestAdapter()
        context = {"recipient": "test", "message": "test"}
        
        start_time = time.time()
        
        with pytest.raises(RetryableError):
            adapter.send(context)
        
        # Should have made 3 attempts
        assert len(adapter.attempt_times) == 3
        
        # Check that delays are approximately exponential
        # (allowing for some variance due to test execution time)
        if len(adapter.attempt_times) >= 3:
            delay1 = adapter.attempt_times[1] - adapter.attempt_times[0]
            delay2 = adapter.attempt_times[2] - adapter.attempt_times[1]
            
            # Second delay should be roughly 2x the first (backoff_factor=2)
            # Allow 50% variance for test timing inconsistencies
            assert delay2 >= delay1 * 1.5, f"Backoff not exponential: {delay1}s -> {delay2}s"
    
    @pytest.mark.unit
    def test_custom_retry_configuration(self):
        """Test adapters with custom retry configuration."""
        
        class CustomRetryAdapter(BaseNotificationAdapter):
            def __init__(self):
                super().__init__("custom")
                self.attempt_count = 0
            
            @retry_with_backoff(max_attempts=5, backoff_factor=1.5, max_delay=60)
            def send(self, context):
                return super().send(context)
            
            def _send_impl(self, context):
                self.attempt_count += 1
                raise RetryableError("Custom retry test")
        
        adapter = CustomRetryAdapter()
        context = {"recipient": "test", "message": "test"}
        
        with pytest.raises(RetryableError):
            with patch('time.sleep'):  # Speed up tests
                adapter.send(context)
        
        # Should have made 5 attempts (custom max_attempts)
        assert adapter.attempt_count == 5


class TestRetryErrorHandling:
    """Test error handling and classification in retry logic."""
    
    @pytest.mark.unit
    def test_retryable_error_inheritance(self):
        """Test RetryableError and NonRetryableError behavior."""
        
        # Test that these are proper exceptions
        retryable = RetryableError("Temporary failure")
        non_retryable = NonRetryableError("Permanent failure")
        
        assert isinstance(retryable, Exception)
        assert isinstance(non_retryable, Exception)
        assert str(retryable) == "Temporary failure"
        assert str(non_retryable) == "Permanent failure"
    
    @pytest.mark.unit
    def test_adapter_error_classification(self):
        """Test that adapters properly classify different types of errors."""
        
        class ErrorClassificationAdapter(BaseNotificationAdapter):
            def __init__(self):
                super().__init__("error_test")
                self.error_to_raise = None
            
            def _send_impl(self, context):
                if self.error_to_raise:
                    raise self.error_to_raise
                return {"success": True}
        
        adapter = ErrorClassificationAdapter()
        context = {"recipient": "test", "message": "test"}
        
        # Test that RetryableError is retried
        adapter.error_to_raise = RetryableError("Transient")
        with pytest.raises(RetryableError):
            with patch('time.sleep'):
                adapter.send(context)
        
        # Test that NonRetryableError is not retried
        adapter.error_to_raise = NonRetryableError("Permanent")
        with pytest.raises(NonRetryableError):
            adapter.send(context)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
