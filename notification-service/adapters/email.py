import logging
from typing import Dict, Any
from core.resilience.base_adapter import BaseNotificationAdapter
from core.resilience.retry import RetryableError, NonRetryableError

logger = logging.getLogger(__name__)

class EmailProvider(BaseNotificationAdapter):
    """Email provider with automatic retry."""
    
    def __init__(self):
        super().__init__("email")
        logger.info("📧 EmailProvider initialized")
    
    def _send_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Send email notification."""
        to_email = context.get('to_email') or context.get('recipient')
        subject = context.get('subject', 'No Subject')
        body = context.get('body') or context.get('message', '')
        
        # Email-specific validation
        if to_email and '@' not in to_email:
            raise NonRetryableError("Invalid email address format")
        
        # Simulate potential failures for testing
        import random
        if random.random() < 0.1:  # 10% chance of retryable error
            raise RetryableError("Email API timeout")
        elif random.random() < 0.05:  # 5% chance of non-retryable error  
            raise NonRetryableError("Invalid API credentials")
        
        # Simulate successful sending
        logger.info(f"📧 Sending email to {to_email}: {subject}")
        
        return {
            "success": True,
            "message_id": f"email_msg_{hash(to_email + subject)}",
            "provider": "email",
            "recipient": to_email,
            "subject": subject
        }
