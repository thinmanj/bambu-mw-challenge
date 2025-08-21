"""
Notification service - CURRENT MONOLITH VERSION
This shows the tightly coupled implementation that needs to be refactored
"""
from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from celery import shared_task
import requests
import logging

from .models import NotificationTemplate, NotificationLog, UserPreference
from identity.models import UserProfile  # COUPLING: Direct reference to another app
from payments.models import Transaction  # COUPLING: Direct reference to another app


logger = logging.getLogger(__name__)


class EmailProvider:
    """Simple email provider - would normally use SendGrid, SES, etc."""
    def send(self, to_email, subject, body):
        # Simulated email sending
        logger.info(f"Sending email to {to_email}: {subject}")
        # In real implementation, this would call SendGrid API
        return True


class SMSProvider:
    """Simple SMS provider - would normally use Twilio, etc."""
    def send(self, phone_number, message):
        # Simulated SMS sending
        logger.info(f"Sending SMS to {phone_number}: {message}")
        # In real implementation, this would call Twilio API
        return True


class PushProvider:
    """Simple push notification provider"""
    def send(self, device_token, title, message):
        # Simulated push sending
        logger.info(f"Sending push to {device_token}: {title}")
        # In real implementation, this would call FCM/APNS
        return True


class NotificationService:
    """
    Main notification service with tight coupling issues
    """
    def __init__(self):
        self.email_provider = EmailProvider()
        self.sms_provider = SMSProvider()
        self.push_provider = PushProvider()
    
    @transaction.atomic
    def send_notification(self, user_id, template_name, context):
        """
        Send a notification to a user
        PROBLEMS:
        - Direct database access
        - No error handling
        - Synchronous sending
        - No retry logic
        - No circuit breaker
        """
        # COUPLING: Direct database access
        user = User.objects.get(id=user_id)
        template = NotificationTemplate.objects.get(name=template_name)
        
        # COUPLING: Accessing related app's model
        user_profile = UserProfile.objects.get(user=user)
        
        # Check user preferences
        try:
            preferences = UserPreference.objects.get(user=user)
        except UserPreference.DoesNotExist:
            preferences = UserPreference.objects.create(user=user)
        
        # Process template with context
        subject = self.render_template(template.subject, context)
        body = self.render_template(template.body, context)
        
        # Create log entry
        log = NotificationLog.objects.create(
            user=user,
            template=template,
            type=template.type,
            status='pending',
            metadata=context
        )
        
        # Send based on type and preferences
        success = False
        error_message = ""
        
        try:
            if template.type == 'email' and preferences.email_enabled:
                success = self.email_provider.send(user.email, subject, body)
            elif template.type == 'sms' and preferences.sms_enabled:
                # COUPLING: Accessing user profile from another app
                phone = user_profile.phone_number
                success = self.sms_provider.send(phone, body)
            elif template.type == 'push' and preferences.push_enabled:
                # COUPLING: Accessing device token from another app
                device_token = user_profile.device_token
                success = self.push_provider.send(device_token, subject, body)
        except Exception as e:
            error_message = str(e)
            logger.error(f"Failed to send notification: {e}")
        
        # Update log
        log.status = 'sent' if success else 'failed'
        log.sent_at = timezone.now() if success else None
        log.error_message = error_message
        log.save()
        
        return success
    
    def render_template(self, template_str, context):
        """Simple template rendering - replaces {key} with values"""
        if not template_str:
            return ""
        
        result = template_str
        for key, value in context.items():
            result = result.replace(f'{{{key}}}', str(value))
        return result
    
    def get_user_notifications(self, user_id, limit=50):
        """
        Get user's notification history
        PERFORMANCE ISSUES:
        - N+1 queries
        - No pagination
        - No caching
        """
        notifications = []
        
        # PROBLEM: Loading all logs for user
        logs = NotificationLog.objects.filter(user_id=user_id).order_by('-created_at')[:limit]
        
        for log in logs:
            # PROBLEM: N+1 query for template
            template = log.template
            
            notifications.append({
                'id': log.id,
                'template_name': template.name if template else 'Unknown',
                'type': log.type,
                'status': log.status,
                'sent_at': log.sent_at,
                'metadata': log.metadata
            })
        
        return notifications
    
    def send_transaction_notification(self, transaction_id):
        """
        Send notification for a transaction
        COUPLING: Direct dependency on payments app
        """
        # PROBLEM: Accessing another app's models directly
        transaction = Transaction.objects.get(id=transaction_id)
        
        context = {
            'amount': transaction.amount,
            'merchant': transaction.merchant_name,
            'date': transaction.created_at.strftime('%Y-%m-%d %H:%M')
        }
        
        return self.send_notification(
            transaction.user_id,
            'transaction_complete',
            context
        )


@shared_task
def send_async_notification(user_id, template_name, context):
    """
    Celery task for async notification sending
    PROBLEMS:
    - No retry configuration
    - No error handling
    - No monitoring
    """
    service = NotificationService()
    return service.send_notification(user_id, template_name, context)


@shared_task
def send_bulk_notifications(user_ids, template_name, context):
    """
    Send notifications to multiple users
    PROBLEMS:
    - No rate limiting
    - No batching
    - No progress tracking
    """
    service = NotificationService()
    results = []
    
    for user_id in user_ids:
        try:
            success = service.send_notification(user_id, template_name, context)
            results.append({'user_id': user_id, 'success': success})
        except Exception as e:
            results.append({'user_id': user_id, 'success': False, 'error': str(e)})
    
    return results