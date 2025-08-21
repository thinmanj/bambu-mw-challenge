"""
Notifications app models - CURRENT MONOLITH VERSION
This is the code you need to extract into a microservice
"""
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField


class NotificationTemplate(models.Model):
    """Template for notifications with variable substitution"""
    NOTIFICATION_TYPES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=255, blank=True)  # For emails
    body = models.TextField()
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    variables = JSONField(default=dict, blank=True)  # Expected variables
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_notificationtemplate'
    
    def __str__(self):
        return f"{self.name} ({self.type})"


class NotificationLog(models.Model):
    """Log of all sent notifications"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=20, choices=NotificationTemplate.NOTIFICATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    metadata = JSONField(default=dict)  # Additional data about the notification
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications_notificationlog'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', 'type']),
        ]
    
    def __str__(self):
        return f"Notification to {self.user.email} - {self.status}"


class UserPreference(models.Model):
    """User notification preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    
    # Quiet hours (in user's timezone)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    # Frequency limits
    max_emails_per_day = models.IntegerField(default=10)
    max_sms_per_day = models.IntegerField(default=5)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_userpreference'
    
    def __str__(self):
        return f"Preferences for {self.user.email}"