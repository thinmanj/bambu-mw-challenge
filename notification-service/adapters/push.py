import logging
from typing import Dict, Any
from core.resilience.base_adapter import BaseNotificationAdapter
from core.resilience.retry import RetryableError, NonRetryableError

logger = logging.getLogger(__name__)

class PushProvider(BaseNotificationAdapter):
    """Push notification provider with automatic retry."""
    
    def __init__(self):
        super().__init__("push")
        logger.info("📢 PushProvider initialized")
    
    def _send_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Send push notification."""
        device_token = context.get('device_token') or context.get('recipient')
        title = context.get('title', 'Notification')
        message = context.get('message') or context.get('body', '')
        
        # Push-specific validation
        if device_token and len(device_token) < 10:
            raise NonRetryableError("Device token too short")
        
        # Simulate potential failures for testing
        import random
        if random.random() < 0.09:  # 9% chance of retryable error
            raise RetryableError("FCM server temporarily unavailable")
        elif random.random() < 0.04:  # 4% chance of non-retryable error
            raise NonRetryableError("Device token is invalid or unregistered")
        
        # Simulate successful sending
        logger.info(f"📢 Sending push to {device_token[:20]}...: {title}")
        
        return {
            "success": True,
            "message_id": f"push_msg_{hash(device_token + title + message)}",
            "provider": "push",
            "recipient": device_token,
            "title": title,
            "message": message
        }
