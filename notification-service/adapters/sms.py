import logging
from typing import Dict, Any
from core.resilience.base_adapter import BaseNotificationAdapter
from core.resilience.retry import RetryableError, NonRetryableError

logger = logging.getLogger(__name__)

class SMSProvider(BaseNotificationAdapter):
    """SMS provider with automatic retry."""
    
    def __init__(self):
        super().__init__("sms")
        logger.info("📱 SMSProvider initialized")
    
    def _send_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Send SMS notification."""
        phone_number = context.get('phone_number') or context.get('recipient')
        message = context.get('message') or context.get('body', '')
        
        # SMS-specific validation
        if phone_number and not (phone_number.startswith('+') or phone_number.replace('-', '').replace(' ', '').isdigit()):
            raise NonRetryableError("Invalid phone number format")
        
        # Simulate potential failures for testing
        import random
        if random.random() < 0.08:  # 8% chance of retryable error
            raise RetryableError("SMS API rate limit exceeded")
        elif random.random() < 0.04:  # 4% chance of non-retryable error
            raise NonRetryableError("Phone number is blocked or invalid")
        
        # Simulate successful sending
        logger.info(f"📱 Sending SMS to {phone_number}: {message[:50]}..." if len(message) > 50 else f"📱 Sending SMS to {phone_number}: {message}")
        
        return {
            "success": True,
            "message_id": f"sms_msg_{hash(phone_number + message)}",
            "provider": "sms",
            "recipient": phone_number,
            "message": message
        }
