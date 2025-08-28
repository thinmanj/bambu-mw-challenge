import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SMSProvider:
    """Simple SMS provider - would normally use Twilio, etc."""
    
    def __init__(self):
        logger.info("📱 SMSProvider initialized")
    
    def send(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send SMS notification.
        Expected context keys: phone_number, message
        """
        phone_number = context.get('phone_number') or context.get('recipient')
        message = context.get('message') or context.get('body', '')
        
        if not phone_number:
            logger.error("❌ SMS sending failed: missing phone number")
            return {
                "success": False,
                "error": "Missing recipient phone number",
                "provider": "sms"
            }
        
        if not message:
            logger.error("❌ SMS sending failed: missing message")
            return {
                "success": False,
                "error": "Missing message content",
                "provider": "sms"
            }
        
        # Simulated SMS sending
        logger.info(f"📱 Sending SMS to {phone_number}: {message[:50]}..." if len(message) > 50 else f"📱 Sending SMS to {phone_number}: {message}")
        
        # In real implementation, this would call Twilio API
        # For now, simulate successful sending
        return {
            "success": True,
            "message_id": f"sms_msg_{hash(phone_number + message)}",
            "provider": "sms",
            "recipient": phone_number,
            "message": message
        }
