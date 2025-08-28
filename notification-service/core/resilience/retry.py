"""
Retry functionality with exponential backoff for notification adapters.

This module provides a retry decorator that implements exponential backoff
for handling transient failures in external service calls.
"""
import functools
import logging
import time
from typing import Callable, Any, Type, Union, Tuple
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)

logger = logging.getLogger(__name__)

# Custom retry exception classes (defined at the end of this module)
class RetryableError(Exception):
    """
    Custom exception that indicates an operation should be retried.
    
    Adapters can raise this exception to signal that an operation
    failed due to a transient error and should be retried.
    """
    pass


class NonRetryableError(Exception):
    """
    Custom exception that indicates an operation should NOT be retried.
    
    Adapters can raise this exception to signal that an operation
    failed due to a permanent error and retrying would be futile.
    """
    pass


# Common exceptions that should trigger retries
RETRYABLE_EXCEPTIONS = (
    RetryableError,
    ConnectionError,
    TimeoutError,
    OSError,
    # Add more as needed for specific providers
)


def retry_with_backoff(
    max_attempts: int = 3,
    backoff_factor: float = 2,
    max_delay: int = 30,
    min_delay: int = 1,
    retry_on: Union[Type[Exception], Tuple[Type[Exception], ...]] = RETRYABLE_EXCEPTIONS,
    log_level: int = logging.WARNING
):
    """
    Decorator factory for retry functionality with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        backoff_factor: Backoff multiplier (default: 2)
        max_delay: Maximum delay between retries in seconds (default: 30)
        min_delay: Minimum delay between retries in seconds (default: 1)
        retry_on: Exception type(s) that should trigger retries
        log_level: Log level for retry messages (default: WARNING)
    
    Returns:
        Decorator function that adds retry logic to the decorated method
        
    Example:
        @retry_with_backoff(max_attempts=3, backoff_factor=2, max_delay=30)
        def send_notification(self, context):
            # implementation
    """
    def decorator(func: Callable) -> Callable:
        # Build the retry decorator using tenacity
        tenacity_decorator = retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=min_delay,
                max=max_delay,
                exp_base=backoff_factor
            ),
            retry=retry_if_exception_type(retry_on),
            before_sleep=before_sleep_log(logger, log_level),
            after=after_log(logger, log_level)
        )
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract method name and class for logging
            method_name = func.__name__
            if args and hasattr(args[0], '__class__'):
                class_name = args[0].__class__.__name__
                full_name = f"{class_name}.{method_name}"
            else:
                full_name = method_name
                
            logger.debug(f"🔄 Starting {full_name} with retry policy: "
                        f"max_attempts={max_attempts}, backoff_factor={backoff_factor}, "
                        f"max_delay={max_delay}s")
            
            try:
                # Apply tenacity retry logic
                return tenacity_decorator(func)(*args, **kwargs)
            except Exception as e:
                # Log final failure after all retries exhausted
                logger.error(f"❌ {full_name} failed after {max_attempts} attempts: {e}")
                # Re-raise the exception to maintain the original behavior
                raise
                
        return wrapper
    return decorator


# Convenience decorators for common retry patterns
def standard_retry(func: Callable) -> Callable:
    """
    Standard retry decorator with typical settings.
    
    - 3 attempts maximum
    - 2x backoff factor
    - 30 second maximum delay
    - 1 second minimum delay
    """
    return retry_with_backoff(max_attempts=3, backoff_factor=2, max_delay=30)(func)


def aggressive_retry(func: Callable) -> Callable:
    """
    Aggressive retry decorator for critical operations.
    
    - 5 attempts maximum
    - 1.5x backoff factor (faster escalation)
    - 60 second maximum delay
    - 1 second minimum delay
    """
    return retry_with_backoff(max_attempts=5, backoff_factor=1.5, max_delay=60)(func)

def gentle_retry(func: Callable) -> Callable:
    """
    Gentle retry decorator for less critical operations.
    
    - 2 attempts maximum
    - 3x backoff factor (slower escalation)
    - 15 second maximum delay
    - 2 second minimum delay
    """
    return retry_with_backoff(max_attempts=2, backoff_factor=3, max_delay=15, min_delay=2)(func)
