"""
GraphQL Resolvers for Notification Service

This module contains all GraphQL query and mutation resolvers.
"""
import strawberry
import json
import logging
import traceback
from typing import List, Optional
from datetime import datetime

from .types import (
    NotificationTemplate, NotificationLog, UserPreference, NotificationResponse,
    NotificationTemplateList, NotificationLogList, PaginationInfo,
    NotificationRequestInput, NotificationTemplateCreateInput, NotificationTemplateUpdateInput,
    NotificationLogUpdateInput, UserPreferenceUpdateInput, PaginationInput, TemplateFilterInput,
    NotificationType, NotificationStatus
)

logger = logging.getLogger(__name__)

# Mock data for demo (same as in main_demo.py)
mock_templates = [
    {
        "id": 1,
        "name": "welcome_email",
        "subject": "Welcome to {app_name}",
        "body": "Hello {user_name}, welcome to our platform!",
        "type": "email",
        "variables": json.dumps({"app_name": "string", "user_name": "string"}),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
]

mock_notifications = [
    {
        "id": 1,
        "user_id": 123,
        "template_id": 1,
        "type": "email",
        "status": "sent",
        "sent_at": datetime.now(),
        "error_message": None,
        "metadata": json.dumps({"provider": "sendgrid", "message_id": "sg_123456"}),
        "created_at": datetime.now(),
        "template": None
    }
]

mock_preferences = {}


def convert_to_graphql_template(template_data: dict) -> NotificationTemplate:
    """Convert template data to GraphQL type"""
    return NotificationTemplate(
        id=template_data["id"],
        name=template_data["name"],
        subject=template_data.get("subject"),
        body=template_data["body"],
        type=NotificationType(template_data["type"]),
        variables=template_data.get("variables"),
        created_at=template_data["created_at"],
        updated_at=template_data["updated_at"]
    )


def convert_to_graphql_notification(notification_data: dict) -> NotificationLog:
    """Convert notification data to GraphQL type"""
    return NotificationLog(
        id=notification_data["id"],
        user_id=notification_data["user_id"],
        template_id=notification_data.get("template_id"),
        type=NotificationType(notification_data["type"]),
        status=NotificationStatus(notification_data["status"]),
        sent_at=notification_data.get("sent_at"),
        error_message=notification_data.get("error_message"),
        metadata=notification_data.get("metadata"),
        created_at=notification_data["created_at"],
        template=None  # Keep simple for demo
    )


def convert_to_graphql_user_preference(preference_data: dict) -> UserPreference:
    """Convert user preference data to GraphQL type"""
    return UserPreference(
        id=preference_data["id"],
        user_id=preference_data["user_id"],
        email_enabled=preference_data["email_enabled"],
        sms_enabled=preference_data["sms_enabled"],
        push_enabled=preference_data["push_enabled"],
        quiet_hours_start=str(preference_data.get("quiet_hours_start")) if preference_data.get("quiet_hours_start") else None,
        quiet_hours_end=str(preference_data.get("quiet_hours_end")) if preference_data.get("quiet_hours_end") else None,
        created_at=preference_data["created_at"],
        updated_at=preference_data["updated_at"]
    )


@strawberry.type
class Query:
    """GraphQL Query resolvers"""

    @strawberry.field
    async def notification_templates(
        self, 
        pagination: Optional[PaginationInput] = None,
        type_filter: Optional[str] = None
    ) -> NotificationTemplateList:
        """Get all notification templates"""
        logger.info(f"📋 GraphQL: Listing templates - type_filter: {type_filter}")
        
        try:
            page = pagination.page if pagination else 1
            size = pagination.size if pagination else 50
            
            filtered = mock_templates
            if type_filter:
                filtered = [t for t in mock_templates if t["type"] == type_filter]
                logger.info(f"🔍 Applied type filter '{type_filter}' - {len(filtered)} templates found")
            
            templates = [convert_to_graphql_template(t) for t in filtered]
            
            logger.info(f"✅ GraphQL: Templates retrieved - total: {len(templates)}")
            
            return NotificationTemplateList(
                items=templates,
                pagination=PaginationInfo(
                    total=len(templates),
                    page=page,
                    size=size,
                    pages=(len(templates) + size - 1) // size
                )
            )
        except Exception as e:
            logger.error(f"💥 GraphQL: Error listing templates - error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    @strawberry.field
    async def notification_template(self, id: int) -> Optional[NotificationTemplate]:
        """Get notification template by ID"""
        logger.info(f"🔍 GraphQL: Getting template details - id: {id}")
        
        for template in mock_templates:
            if template["id"] == id:
                logger.info(f"✅ GraphQL: Template found - id: {id}")
                return convert_to_graphql_template(template)
        
        logger.warning(f"⚠️ GraphQL: Template not found - id: {id}")
        return None

    @strawberry.field
    async def notification(self, id: int) -> Optional[NotificationLog]:
        """Get notification by ID"""
        logger.info(f"🔍 GraphQL: Getting notification details - id: {id}")
        
        for notif in mock_notifications:
            if notif["id"] == id:
                logger.info(f"✅ GraphQL: Notification found - id: {id}")
                return convert_to_graphql_notification(notif)
        
        logger.warning(f"⚠️ GraphQL: Notification not found - id: {id}")
        return None

    @strawberry.field
    async def user_notifications(
        self, 
        user_id: int, 
        pagination: Optional[PaginationInput] = None
    ) -> NotificationLogList:
        """Get notifications for a specific user"""
        logger.info(f"📋 GraphQL: Listing user notifications - user_id: {user_id}")
        
        page = pagination.page if pagination else 1
        size = pagination.size if pagination else 50
        
        user_notifications = [n for n in mock_notifications if n.get("user_id") == user_id]
        notification_logs = [convert_to_graphql_notification(n) for n in user_notifications]
        
        logger.info(f"✅ GraphQL: User notifications retrieved - user_id: {user_id}, count: {len(notification_logs)}")
        
        return NotificationLogList(
            items=notification_logs,
            pagination=PaginationInfo(
                total=len(notification_logs),
                page=page,
                size=size,
                pages=(len(notification_logs) + size - 1) // size
            )
        )

    @strawberry.field
    async def user_preferences(self, user_id: int) -> UserPreference:
        """Get user preferences"""
        logger.info(f"📊 GraphQL: Getting user preferences - user_id: {user_id}")
        
        if user_id not in mock_preferences:
            logger.info(f"🆕 GraphQL: Creating default preferences for user - user_id: {user_id}")
            mock_preferences[user_id] = {
                "id": user_id,
                "user_id": user_id,
                "email_enabled": True,
                "sms_enabled": True,
                "push_enabled": True,
                "quiet_hours_start": None,
                "quiet_hours_end": None,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        
        logger.info(f"✅ GraphQL: User preferences retrieved - user_id: {user_id}")
        return convert_to_graphql_user_preference(mock_preferences[user_id])


@strawberry.type
class Mutation:
    """GraphQL Mutation resolvers"""

    @strawberry.mutation
    async def send_notification(self, input: NotificationRequestInput) -> NotificationResponse:
        """Send a notification"""
        logger.info(f"🚀 GraphQL: Sending notification - user_id: {input.user_id}, template: {input.template_name}")
        
        try:
            # Parse context JSON
            try:
                context = json.loads(input.context)
            except json.JSONDecodeError:
                logger.error(f"❌ GraphQL: Invalid JSON in context - {input.context}")
                raise Exception("Invalid JSON in context field")
            
            # Find the template by name
            template_found = None
            template_id = None
            template_type = NotificationType.EMAIL  # Default
            
            for template in mock_templates:
                if template["name"] == input.template_name:
                    template_found = template
                    template_id = template["id"]
                    template_type = NotificationType(template["type"])
                    logger.info(f"✅ GraphQL: Template found - id: {template_id}, type: {template_type}")
                    break
            
            if not template_found:
                logger.error(f"❌ GraphQL: Template not found - name: {input.template_name}")
                raise Exception(f"Template '{input.template_name}' not found")
            
            # Create notification log entry
            notification_log = {
                "id": len(mock_notifications) + 1,
                "user_id": input.user_id,
                "template_id": template_id,
                "type": template_type.value,
                "status": NotificationStatus.PENDING.value,
                "sent_at": None,
                "error_message": None,
                "metadata": json.dumps({
                    "template_name": input.template_name,
                    "context": context,
                    "rendered_subject": template_found.get("subject", ""),
                    "rendered_body": template_found.get("body", "")
                }),
                "created_at": datetime.now(),
                "template": None
            }
            mock_notifications.append(notification_log)
            
            logger.info(f"✅ GraphQL: Notification created successfully - id: {notification_log['id']}, user_id: {input.user_id}")
            
            return NotificationResponse(
                id=notification_log["id"],
                status=NotificationStatus.PENDING,
                message=f"Notification queued for user {input.user_id} using template '{input.template_name}'",
                created_at=notification_log["created_at"]
            )
            
        except Exception as e:
            logger.error(f"💥 GraphQL: Unexpected error sending notification - user_id: {input.user_id}, error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    @strawberry.mutation
    async def create_notification_template(self, input: NotificationTemplateCreateInput) -> NotificationTemplate:
        """Create a new notification template"""
        logger.info(f"📝 GraphQL: Creating template - name: {input.name}, type: {input.type}")
        
        try:
            template = {
                "id": len(mock_templates) + 1,
                "name": input.name,
                "subject": input.subject,
                "body": input.body,
                "type": input.type.value,
                "variables": input.variables,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            mock_templates.append(template)
            
            logger.info(f"✅ GraphQL: Template created successfully - id: {template['id']}, name: {template['name']}")
            
            return convert_to_graphql_template(template)
            
        except Exception as e:
            logger.error(f"💥 GraphQL: Error creating template - name: {input.name}, error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    @strawberry.mutation
    async def update_notification_template(self, id: int, input: NotificationTemplateUpdateInput) -> Optional[NotificationTemplate]:
        """Update a notification template"""
        logger.info(f"🔧 GraphQL: Updating template - id: {id}")
        
        try:
            for i, template in enumerate(mock_templates):
                if template["id"] == id:
                    # Update only provided fields
                    if input.name is not None:
                        template["name"] = input.name
                    if input.subject is not None:
                        template["subject"] = input.subject
                    if input.body is not None:
                        template["body"] = input.body
                    if input.type is not None:
                        template["type"] = input.type.value
                    if input.variables is not None:
                        template["variables"] = input.variables
                    
                    template["updated_at"] = datetime.now()
                    
                    logger.info(f"✅ GraphQL: Template updated successfully - id: {id}")
                    return convert_to_graphql_template(template)
            
            logger.warning(f"⚠️ GraphQL: Template not found for update - id: {id}")
            return None
            
        except Exception as e:
            logger.error(f"💥 GraphQL: Error updating template - id: {id}, error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    @strawberry.mutation
    async def delete_notification_template(self, id: int) -> bool:
        """Delete a notification template"""
        logger.info(f"🗑️ GraphQL: Deleting template - id: {id}")
        
        try:
            for i, template in enumerate(mock_templates):
                if template["id"] == id:
                    mock_templates.pop(i)
                    logger.info(f"✅ GraphQL: Template deleted successfully - id: {id}")
                    return True
            
            logger.warning(f"⚠️ GraphQL: Template not found for deletion - id: {id}")
            return False
            
        except Exception as e:
            logger.error(f"💥 GraphQL: Error deleting template - id: {id}, error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    @strawberry.mutation
    async def update_notification_status(self, id: int, input: NotificationLogUpdateInput) -> Optional[NotificationLog]:
        """Update notification status"""
        logger.info(f"🔧 GraphQL: Updating notification status - id: {id}")
        
        try:
            for i, notification in enumerate(mock_notifications):
                if notification["id"] == id:
                    # Update only provided fields
                    if input.status is not None:
                        notification["status"] = input.status.value
                    if input.sent_at is not None:
                        notification["sent_at"] = input.sent_at
                    if input.error_message is not None:
                        notification["error_message"] = input.error_message
                    if input.metadata is not None:
                        notification["metadata"] = input.metadata
                    
                    logger.info(f"✅ GraphQL: Notification status updated - id: {id}")
                    return convert_to_graphql_notification(notification)
            
            logger.warning(f"⚠️ GraphQL: Notification not found for status update - id: {id}")
            return None
            
        except Exception as e:
            logger.error(f"💥 GraphQL: Error updating notification status - id: {id}, error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    @strawberry.mutation
    async def update_user_preferences(self, user_id: int, input: UserPreferenceUpdateInput) -> UserPreference:
        """Update user preferences"""
        logger.info(f"🔧 GraphQL: Updating user preferences - user_id: {user_id}")
        
        try:
            if user_id not in mock_preferences:
                logger.info(f"🆕 GraphQL: Creating default preferences before update - user_id: {user_id}")
                mock_preferences[user_id] = {
                    "id": user_id,
                    "user_id": user_id,
                    "email_enabled": True,
                    "sms_enabled": True,
                    "push_enabled": True,
                    "quiet_hours_start": None,
                    "quiet_hours_end": None,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            
            # Update only provided fields
            if input.email_enabled is not None:
                mock_preferences[user_id]["email_enabled"] = input.email_enabled
            if input.sms_enabled is not None:
                mock_preferences[user_id]["sms_enabled"] = input.sms_enabled
            if input.push_enabled is not None:
                mock_preferences[user_id]["push_enabled"] = input.push_enabled
            if input.quiet_hours_start is not None:
                mock_preferences[user_id]["quiet_hours_start"] = input.quiet_hours_start
            if input.quiet_hours_end is not None:
                mock_preferences[user_id]["quiet_hours_end"] = input.quiet_hours_end
            
            mock_preferences[user_id]["updated_at"] = datetime.now()
            
            logger.info(f"✅ GraphQL: User preferences updated successfully - user_id: {user_id}")
            
            return convert_to_graphql_user_preference(mock_preferences[user_id])
            
        except Exception as e:
            logger.error(f"💥 GraphQL: Error updating user preferences - user_id: {user_id}, error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise


# Create the schema
schema = strawberry.Schema(query=Query, mutation=Mutation)
