"""
Unit tests for tenacity integration and retry interface.

This module specifically tests the tenacity library integration,
retry decorators, and the exponential backoff behavior.
"""
import pytest
import time
from unittest.mock import Mock, patch, call
import logging
from tenacity import RetryError, stop_after_attempt, wait_exponential
from core.resilience.retry import (
    retry_with_backoff, 
    RetryableError, 
    NonRetryableError,
    standard_retry,
    aggressive_retry,
    gentle_retry,
    RETRYABLE_EXCEPTIONS
)


class TestTenacityInterface:
    """Test tenacity library interface and basic functionality."""
    
    @pytest.mark.unit
    def test_tenacity_retry_error_is_raised_after_max_attempts(self):
        """Test that tenacity.RetryError is raised after max attempts."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=2, backoff_factor=1.1, max_delay=5)
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Always fails")
        
        with pytest.raises(RetryError) as exc_info:
            with patch('time.sleep'):  # Speed up tests
                failing_function()
        
        # Verify the retry error contains our original exception
        assert "ConnectionError" in str(exc_info.value)
        assert call_count == 2  # Called exactly max_attempts times
    
    @pytest.mark.unit
    def test_tenacity_exponential_wait_configuration(self):
        """Test that tenacity's wait_exponential is configured correctly."""
        delays = []
        original_sleep = time.sleep
        
        def mock_sleep(duration):
            delays.append(duration)
        
        @retry_with_backoff(max_attempts=4, backoff_factor=2, max_delay=10, min_delay=1)
        def test_function():
            raise ConnectionError("Test error")
        
        with patch('time.sleep', side_effect=mock_sleep):
            with pytest.raises(RetryError):
                test_function()
        
        # Verify exponential backoff pattern: 1, 2, 4 (capped at max_delay=10)
        assert len(delays) == 3  # 3 retries for 4 attempts
        assert delays[0] >= 1.0  # First delay >= min_delay
        assert delays[1] >= delays[0] * 1.5  # Exponential growth
        assert delays[2] >= delays[1] * 1.5  # Continued growth
        assert all(delay <= 10 for delay in delays)  # Capped at max_delay
    
    @pytest.mark.unit
    def test_tenacity_stop_after_attempt_configuration(self):
        """Test that tenacity's stop_after_attempt is configured correctly."""
        attempts = []
        
        @retry_with_backoff(max_attempts=5, backoff_factor=2, max_delay=30)
        def counting_function():
            attempts.append(len(attempts) + 1)
            raise TimeoutError("Counting attempts")
        
        with pytest.raises(RetryError):
            with patch('time.sleep'):  # Speed up tests
                counting_function()
        
        assert len(attempts) == 5  # Exactly max_attempts
        assert attempts == [1, 2, 3, 4, 5]  # Sequential attempts
    
    @pytest.mark.unit
    def test_tenacity_retry_condition_respects_exception_types(self):
        """Test that tenacity only retries on specified exception types."""
        retry_attempts = []
        
        @retry_with_backoff(max_attempts=3, retry_on=(ConnectionError, TimeoutError))
        def selective_retry_function(error_type):
            retry_attempts.append(len(retry_attempts) + 1)
            if error_type == "connection":
                raise ConnectionError("Network issue")
            elif error_type == "timeout":
                raise TimeoutError("Request timeout")
            else:
                raise ValueError("Invalid value")
        
        # Test ConnectionError is retried
        retry_attempts.clear()
        with pytest.raises(RetryError):
            with patch('time.sleep'):
                selective_retry_function("connection")
        assert len(retry_attempts) == 3
        
        # Test TimeoutError is retried  
        retry_attempts.clear()
        with pytest.raises(RetryError):
            with patch('time.sleep'):
                selective_retry_function("timeout")
        assert len(retry_attempts) == 3
        
        # Test ValueError is NOT retried
        retry_attempts.clear()
        with pytest.raises(ValueError):
            selective_retry_function("value")
        assert len(retry_attempts) == 1  # Only called once, no retries


class TestRetryDecorators:
    """Test retry decorator implementations and configurations."""
    
    @pytest.mark.unit
    def test_standard_retry_decorator_configuration(self):
        """Test that standard_retry uses correct default values."""
        call_count = 0
        
        @standard_retry
        def test_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Standard retry test")
        
        with pytest.raises(RetryError):
            with patch('time.sleep'):
                test_func()
        
        # standard_retry should attempt 3 times by default
        assert call_count == 3
    
    @pytest.mark.unit
    def test_aggressive_retry_decorator_configuration(self):
        """Test that aggressive_retry uses more attempts."""
        call_count = 0
        
        @aggressive_retry
        def test_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Aggressive retry test")
        
        with pytest.raises(RetryError):
            with patch('time.sleep'):
                test_func()
        
        # aggressive_retry should attempt 5 times
        assert call_count == 5
    
    @pytest.mark.unit
    def test_gentle_retry_decorator_configuration(self):
        """Test that gentle_retry uses fewer attempts."""
        call_count = 0
        
        @gentle_retry
        def test_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Gentle retry test")
        
        with pytest.raises(RetryError):
            with patch('time.sleep'):
                test_func()
        
        # gentle_retry should attempt only 2 times
        assert call_count == 2
    
    @pytest.mark.unit
    def test_custom_retry_configuration_override(self):
        """Test that custom retry configurations work correctly."""
        call_count = 0
        delays = []
        
        def mock_sleep(duration):
            delays.append(duration)
        
        @retry_with_backoff(max_attempts=3, backoff_factor=3, max_delay=20, min_delay=2)
        def custom_func():
            nonlocal call_count
            call_count += 1
            raise OSError("Custom configuration test")
        
        with patch('time.sleep', side_effect=mock_sleep):
            with pytest.raises(RetryError):
                custom_func()
        
        assert call_count == 3  # Custom max_attempts
        assert len(delays) == 2  # 2 retries for 3 attempts
        assert all(delay >= 2.0 for delay in delays)  # min_delay = 2
        assert all(delay <= 20.0 for delay in delays)  # max_delay = 20
    
    @pytest.mark.unit
    def test_retry_decorator_preserves_function_metadata(self):
        """Test that retry decorator preserves original function metadata."""
        
        @retry_with_backoff(max_attempts=2)
        def documented_function():
            """This is a test function with documentation."""
            return "success"
        
        # Check that function metadata is preserved
        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a test function with documentation."


class TestExceptionClassification:
    """Test exception classification for retry logic."""
    
    @pytest.mark.unit
    def test_retryable_exceptions_list(self):
        """Test that RETRYABLE_EXCEPTIONS contains expected types."""
        expected_exceptions = (
            RetryableError,
            ConnectionError,
            TimeoutError,
            OSError
        )
        
        for exc_type in expected_exceptions:
            assert exc_type in RETRYABLE_EXCEPTIONS
        
        # Test that custom exceptions work
        assert issubclass(RetryableError, Exception)
        assert issubclass(NonRetryableError, Exception)
    
    @pytest.mark.unit
    def test_retryable_error_behavior(self):
        """Test RetryableError triggers retries."""
        call_count = 0
        
        @retry_with_backoff(max_attempts=3)
        def retryable_error_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RetryableError("This should be retried")
            return "success after retries"
        
        with patch('time.sleep'):
            result = retryable_error_func()
        
        assert result == "success after retries"
        assert call_count == 3  # Failed twice, succeeded on third attempt
    
    @pytest.mark.unit 
    def test_non_retryable_error_behavior(self):
        """Test NonRetryableError does not trigger retries."""
        call_count = 0
        
        # Use default RETRYABLE_EXCEPTIONS which does NOT include NonRetryableError
        @retry_with_backoff(max_attempts=3, retry_on=RETRYABLE_EXCEPTIONS)
        def non_retryable_error_func():
            nonlocal call_count
            call_count += 1
            raise NonRetryableError("This should not be retried")
        
        # NonRetryableError is not in RETRYABLE_EXCEPTIONS, so no retry
        with pytest.raises(NonRetryableError):
            non_retryable_error_func()
        
        assert call_count == 1  # Called only once, no retries
    
    @pytest.mark.unit
    def test_mixed_exception_scenarios(self):
        """Test behavior with mixed retryable and non-retryable exceptions."""
        call_sequence = []
        
        @retry_with_backoff(max_attempts=4, retry_on=(RetryableError, ConnectionError))
        def mixed_errors_func(scenario):
            call_sequence.append(len(call_sequence) + 1)
            
            if scenario == "retryable_then_success":
                if len(call_sequence) < 3:
                    raise RetryableError("Temporary failure")
                return "success"
            elif scenario == "non_retryable":
                raise ValueError("Permanent failure")
        
        # Test retryable error followed by success
        call_sequence.clear()
        with patch('time.sleep'):
            result = mixed_errors_func("retryable_then_success")
        assert result == "success"
        assert len(call_sequence) == 3
        
        # Test non-retryable error (not retried)
        call_sequence.clear()
        with pytest.raises(ValueError):
            mixed_errors_func("non_retryable")
        assert len(call_sequence) == 1


class TestTenacityLogging:
    """Test logging integration with tenacity."""
    
    @pytest.mark.unit
    def test_retry_logging_messages(self):
        """Test that retry attempts are logged correctly."""
        
        @retry_with_backoff(max_attempts=3, log_level=logging.INFO)
        def logged_function():
            raise ConnectionError("Test logging")
        
        with patch('time.sleep'):
            with patch('core.resilience.retry.logger') as mock_logger:
                with pytest.raises(RetryError):
                    logged_function()
                
                # Check that appropriate logging calls were made
                mock_logger.debug.assert_called()
                mock_logger.error.assert_called()
    
    @pytest.mark.unit
    def test_before_sleep_logging(self):
        """Test that before_sleep logging works correctly."""
        
        @retry_with_backoff(max_attempts=2, log_level=logging.WARNING)
        def before_sleep_func():
            raise TimeoutError("Before sleep test")
        
        # Capture the tenacity before_sleep logs
        with patch('time.sleep'):
            with pytest.raises(RetryError):
                with patch('logging.getLogger') as mock_get_logger:
                    mock_logger = Mock()
                    mock_get_logger.return_value = mock_logger
                    
                    before_sleep_func()
    
    @pytest.mark.unit
    def test_function_name_extraction_in_logging(self):
        """Test that function names are correctly extracted for logging."""
        
        class TestClass:
            @retry_with_backoff(max_attempts=2)
            def test_method(self):
                raise ConnectionError("Method test")
        
        test_instance = TestClass()
        
        with patch('time.sleep'):
            with patch('core.resilience.retry.logger') as mock_logger:
                with pytest.raises(RetryError):
                    test_instance.test_method()
                
                # Verify that the logging includes class and method names
                debug_calls = mock_logger.debug.call_args_list
                error_calls = mock_logger.error.call_args_list
                
                # Check that at least one call contains the expected method info
                found_method_name = False
                for call_args in debug_calls + error_calls:
                    if "TestClass.test_method" in str(call_args):
                        found_method_name = True
                        break
                
                assert found_method_name, "Method name not found in logging calls"


class TestTenacityEdgeCases:
    """Test edge cases and error conditions in tenacity integration."""
    
    @pytest.mark.unit
    def test_zero_max_attempts_configuration(self):
        """Test behavior with invalid max_attempts configuration."""
        
        # tenacity should handle this gracefully
        @retry_with_backoff(max_attempts=0)
        def zero_attempts_func():
            return "should work immediately"
        
        # With 0 max_attempts, function should still be called at least once
        result = zero_attempts_func()
        assert result == "should work immediately"
    
    @pytest.mark.unit
    def test_very_large_backoff_factor(self):
        """Test behavior with very large backoff factors."""
        delays = []
        
        def mock_sleep(duration):
            delays.append(duration)
        
        @retry_with_backoff(max_attempts=3, backoff_factor=100, max_delay=5, min_delay=1)
        def large_backoff_func():
            raise ConnectionError("Large backoff test")
        
        with patch('time.sleep', side_effect=mock_sleep):
            with pytest.raises(RetryError):
                large_backoff_func()
        
        # Even with large backoff_factor, delays should be capped at max_delay
        assert all(delay <= 5.0 for delay in delays), f"Delays not capped: {delays}"
    
    @pytest.mark.unit
    def test_negative_delay_configuration(self):
        """Test behavior with negative delay configurations."""
        
        # tenacity should handle negative values gracefully
        @retry_with_backoff(max_attempts=2, min_delay=-1, max_delay=-1)
        def negative_delay_func():
            raise ConnectionError("Negative delay test")
        
        # Should not crash, tenacity handles this internally
        with patch('time.sleep'):
            with pytest.raises(RetryError):
                negative_delay_func()
    
    @pytest.mark.unit
    def test_success_after_partial_retries(self):
        """Test success after some but not all retry attempts."""
        call_history = []
        
        @retry_with_backoff(max_attempts=5)
        def partial_retry_func():
            call_history.append(len(call_history) + 1)
            if len(call_history) <= 3:
                raise ConnectionError(f"Attempt {len(call_history)} failed")
            return f"Success on attempt {len(call_history)}"
        
        with patch('time.sleep'):
            result = partial_retry_func()
        
        assert result == "Success on attempt 4"
        assert call_history == [1, 2, 3, 4]  # Failed 3 times, succeeded on 4th
    
    @pytest.mark.unit
    def test_exception_chaining_in_retry_error(self):
        """Test that original exceptions are properly chained in RetryError."""
        original_exception = ConnectionError("Original failure")
        
        @retry_with_backoff(max_attempts=2)
        def chaining_func():
            raise original_exception
        
        with patch('time.sleep'):
            with pytest.raises(RetryError) as exc_info:
                chaining_func()
        
        # Verify that the original exception is accessible
        retry_error = exc_info.value
        assert retry_error is not None
        # The original exception should be in the retry error's context
        assert "ConnectionError" in str(retry_error)
        assert "Original failure" in str(retry_error)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
