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
        if not isinstance(context, dict):
            raise NonRetryableError("Invalid context")
        
        if not context:  # Empty dict case
            raise NonRetryableError("Missing recipient")
        
        # Check for required fields
        recipient_keys = ['recipient', 'to_email', 'phone_number', 'device_token']
        def is_valid_field(value):
            return value is not None and str(value).strip()
        
        # Check if any recipient field exists (even if empty) - let adapters handle their own validation
        if not any(key in context for key in recipient_keys):
            raise NonRetryableError("Missing recipient")
        
        # Only validate recipient content if ALL recipient fields are empty/None - let adapters handle details
        if not any(context.get(key) is not None for key in recipient_keys):
            raise NonRetryableError("Missing recipient")
        
        message_keys = ['message', 'body', 'subject']
        def message_field_exists(key):
            value = context.get(key)
            return value is not None and value != ''  # Allow whitespace-only but not None or empty string
        
        if not any(message_field_exists(key) for key in message_keys):
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
