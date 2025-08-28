"""
Minimal base class for notification adapters with retry functionality.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from .retry import retry_with_backoff, RetryableError, NonRetryableError


class BaseNotificationAdapter(ABC):
    """
    Minimal base class for notification adapters with built-in retry.
    """
    
    def __init__(self, adapter_name: str):
        self.adapter_name = adapter_name
    
    @retry_with_backoff(max_attempts=3, backoff_factor=2, max_delay=30)
    def send(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification with retry logic."""
        # Basic validation
        if not context or not isinstance(context, dict):
            raise NonRetryableError("Invalid context")
        
        # Check for required fields
        recipient_keys = ['recipient', 'to_email', 'phone_number', 'device_token']
        if not any(key in context for key in recipient_keys):
            raise NonRetryableError("Missing recipient")
        
        message_keys = ['message', 'body', 'subject']
        if not any(context.get(key) for key in message_keys):
            raise NonRetryableError("Missing message")
        
        # Call implementation
        try:
            return self._send_impl(context)
        except (RetryableError, NonRetryableError):
            raise
        except Exception as e:
            # Convert unknown errors to retryable
            raise RetryableError(f"Unexpected error: {e}") from e
    
    @abstractmethod
    def _send_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation-specific sending logic."""
        pass
