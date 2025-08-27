import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from math import ceil

from core.models import (
    NotificationTemplate, NotificationLog, UserPreference, NotificationStatus
)
from api.v1.schemas import (
    NotificationRequest, NotificationResponse,
    NotificationTemplateCreate, NotificationTemplateUpdate,
    NotificationLogCreate, NotificationLogUpdate,
    UserPreferenceCreate, UserPreferenceUpdate,
    NotificationTemplateList, NotificationLogList, UserPreferenceList
)
from core.repositories import (
    NotificationTemplateRepository,
    NotificationLogRepository,
    UserPreferenceRepository,
)
from database.connection import get_redis_client


class NotificationTemplateService:
    """Service layer for notification templates"""
    
    def __init__(self, db: AsyncSession):
        self.repository = NotificationTemplateRepository(db)
    
    async def create_template(self, template_data: NotificationTemplateCreate) -> NotificationTemplate:
        """Create a new notification template"""
        return await self.repository.create(template_data)
    
    async def get_template(self, template_id: int) -> Optional[NotificationTemplate]:
        """Get template by ID"""
        return await self.repository.get_by_id(template_id)
    
    async def get_template_by_name(self, name: str) -> Optional[NotificationTemplate]:
        """Get template by name"""
        return await self.repository.get_by_name(name)
    
    async def list_templates(
        self,
        page: int = 1,
        size: int = 50,
        type_filter: Optional[str] = None
    ) -> NotificationTemplateList:
        """List templates with pagination"""
        skip = (page - 1) * size
        items = await self.repository.get_all(skip, size, type_filter)
        total = await self.repository.count(type_filter)
        pages = ceil(total / size) if total > 0 else 1
        
        return NotificationTemplateList(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    
    async def update_template(
        self,
        template_id: int,
        template_data: NotificationTemplateUpdate
    ) -> Optional[NotificationTemplate]:
        """Update an existing template"""
        return await self.repository.update(template_id, template_data)
    
    async def delete_template(self, template_id: int) -> bool:
        """Delete a template"""
        return await self.repository.delete(template_id)


class NotificationLogService:
    """Service layer for notification logs"""
    
    def __init__(self, db: AsyncSession):
        self.repository = NotificationLogRepository(db)
    
    async def create_log(self, log_data: NotificationLogCreate) -> NotificationLog:
        """Create a new notification log entry"""
        return await self.repository.create(log_data)
    
    async def get_log(self, log_id: int) -> Optional[NotificationLog]:
        """Get log by ID"""
        return await self.repository.get_by_id(log_id)
    
    async def get_user_logs(
        self,
        user_id: int,
        page: int = 1,
        size: int = 50
    ) -> NotificationLogList:
        """Get logs for a specific user"""
        skip = (page - 1) * size
        items = await self.repository.get_by_user_id(user_id, skip, size)
        total = await self.repository.count(user_id=user_id)
        pages = ceil(total / size) if total > 0 else 1
        
        return NotificationLogList(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    
    async def list_logs(
        self,
        page: int = 1,
        size: int = 50,
        status_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> NotificationLogList:
        """List logs with optional filtering"""
        skip = (page - 1) * size
        items = await self.repository.get_all(
            skip, size, status_filter, type_filter, user_id
        )
        total = await self.repository.count(status_filter, type_filter, user_id)
        pages = ceil(total / size) if total > 0 else 1
        
        return NotificationLogList(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    
    async def update_log(
        self,
        log_id: int,
        log_data: NotificationLogUpdate
    ) -> Optional[NotificationLog]:
        """Update an existing log entry"""
        return await self.repository.update(log_id, log_data)


class UserPreferenceService:
    """Service layer for user preferences"""
    
    def __init__(self, db: AsyncSession):
        self.repository = UserPreferenceRepository(db)
    
    async def get_user_preference(self, user_id: int) -> Optional[UserPreference]:
        """Get user preference by user ID"""
        return await self.repository.get_by_user_id(user_id)
    
    async def create_user_preference(
        self,
        preference_data: UserPreferenceCreate
    ) -> UserPreference:
        """Create user preferences"""
        return await self.repository.create(preference_data)
    
    async def update_user_preference(
        self,
        user_id: int,
        preference_data: UserPreferenceUpdate,
    ) -> Optional[UserPreference]:
        """Update user preferences"""
        return await self.repository.update(user_id, preference_data)
    
    async def upsert_user_preference(
        self,
        user_id: int,
        preference_data: UserPreferenceCreate,
    ) -> UserPreference:
        """Get existing preferences or create with defaults"""
        return await self.repository.upsert(user_id, preference_data)
    
    async def delete_user_preference(self, user_id: int) -> bool:
        """Delete user preferences"""
        return await self.repository.delete(user_id)
    
    async def list_preferences(
        self,
        page: int = 1,
        size: int = 50
    ) -> UserPreferenceList:
        """List user preferences with pagination"""
        skip = (page - 1) * size
        items = await self.repository.get_all(skip, size)
        total = await self.repository.count()
        pages = ceil(total / size) if total > 0 else 1
        
        return UserPreferenceList(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )


class NotificationService:
    """Legacy notification service for backward compatibility"""
    
    async def send_notification(self, request: NotificationRequest) -> NotificationResponse:
        """Send a notification (minimal implementation)"""
        notification_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        # Store notification status in Redis for quick lookup
        redis_client = await get_redis_client()
        notification_data = {
            "id": notification_id,
            "status": NotificationStatus.PENDING.value,
            "recipient": request.recipient,
            "type": request.type.value,
            "message": request.message,
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat()
        }
        
        await redis_client.hset(
            f"notification:{notification_id}",
            mapping=notification_data
        )
        
        # TODO: Implement actual sending logic using adapters
        # For now, just return a pending response
        
        return NotificationResponse(
            id=notification_id,
            status=NotificationStatus.PENDING,
            message=f"Notification queued for {request.recipient}",
            created_at=created_at
        )
    
