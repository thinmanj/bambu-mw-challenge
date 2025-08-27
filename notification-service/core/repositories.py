from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, desc, func

from core.models import NotificationTemplate, NotificationLog, UserPreference
from core.schemas import (
    NotificationTemplateCreate, NotificationTemplateUpdate,
    NotificationLogCreate, NotificationLogUpdate,
    UserPreferenceCreate, UserPreferenceUpdate
)


class NotificationTemplateRepository:
    """Repository for notification template operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, template_id: int) -> Optional[NotificationTemplate]:
        """Get template by ID"""
        result = await self.db.execute(
            select(NotificationTemplate).where(NotificationTemplate.id == template_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[NotificationTemplate]:
        """Get template by name"""
        result = await self.db.execute(
            select(NotificationTemplate).where(NotificationTemplate.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        type_filter: Optional[str] = None
    ) -> List[NotificationTemplate]:
        """Get all templates with pagination"""
        query = select(NotificationTemplate)
        
        if type_filter:
            query = query.where(NotificationTemplate.type == type_filter)
        
        query = query.offset(skip).limit(limit).order_by(desc(NotificationTemplate.created_at))
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count(self, type_filter: Optional[str] = None) -> int:
        """Count templates"""
        query = select(func.count(NotificationTemplate.id))
        
        if type_filter:
            query = query.where(NotificationTemplate.type == type_filter)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def create(self, template_data: NotificationTemplateCreate) -> NotificationTemplate:
        """Create new template"""
        template = NotificationTemplate(**template_data.model_dump())
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def update(
        self, 
        template_id: int, 
        template_data: NotificationTemplateUpdate
    ) -> Optional[NotificationTemplate]:
        """Update existing template"""
        template = await self.get_by_id(template_id)
        if not template:
            return None
        
        update_data = template_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)
        
        await self.db.commit()
        await self.db.refresh(template)
        return template
    
    async def delete(self, template_id: int) -> bool:
        """Delete template"""
        template = await self.get_by_id(template_id)
        if not template:
            return False
        
        await self.db.delete(template)
        await self.db.commit()
        return True


class NotificationLogRepository:
    """Repository for notification log operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, log_id: int) -> Optional[NotificationLog]:
        """Get log by ID with template relation"""
        result = await self.db.execute(
            select(NotificationLog)
            .options(selectinload(NotificationLog.template))
            .where(NotificationLog.id == log_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[NotificationLog]:
        """Get logs by user ID"""
        result = await self.db.execute(
            select(NotificationLog)
            .options(selectinload(NotificationLog.template))
            .where(NotificationLog.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(desc(NotificationLog.created_at))
        )
        return list(result.scalars().all())
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> List[NotificationLog]:
        """Get all logs with filters"""
        query = select(NotificationLog).options(selectinload(NotificationLog.template))
        
        conditions = []
        if status_filter:
            conditions.append(NotificationLog.status == status_filter)
        if type_filter:
            conditions.append(NotificationLog.type == type_filter)
        if user_id:
            conditions.append(NotificationLog.user_id == user_id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.offset(skip).limit(limit).order_by(desc(NotificationLog.created_at))
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count(
        self,
        status_filter: Optional[str] = None,
        type_filter: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> int:
        """Count logs with filters"""
        query = select(func.count(NotificationLog.id))
        
        conditions = []
        if status_filter:
            conditions.append(NotificationLog.status == status_filter)
        if type_filter:
            conditions.append(NotificationLog.type == type_filter)
        if user_id:
            conditions.append(NotificationLog.user_id == user_id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def create(self, log_data: NotificationLogCreate) -> NotificationLog:
        """Create new log entry"""
        log = NotificationLog(**log_data.model_dump())
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        return log
    
    async def update(
        self, 
        log_id: int, 
        log_data: NotificationLogUpdate
    ) -> Optional[NotificationLog]:
        """Update existing log"""
        log = await self.get_by_id(log_id)
        if not log:
            return None
        
        update_data = log_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(log, field, value)
        
        await self.db.commit()
        await self.db.refresh(log)
        return log


class UserPreferenceRepository:
    """Repository for user preference operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, preference_id: int) -> Optional[UserPreference]:
        """Get preference by ID"""
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.id == preference_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: int) -> Optional[UserPreference]:
        """Get preference by user ID"""
        result = await self.db.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[UserPreference]:
        """Get all preferences"""
        result = await self.db.execute(
            select(UserPreference)
            .offset(skip)
            .limit(limit)
            .order_by(desc(UserPreference.updated_at))
        )
        return list(result.scalars().all())
    
    async def count(self) -> int:
        """Count preferences"""
        result = await self.db.execute(select(func.count(UserPreference.id)))
        return result.scalar() or 0
    
    async def create(self, preference_data: UserPreferenceCreate) -> UserPreference:
        """Create new user preference"""
        preference = UserPreference(**preference_data.model_dump())
        self.db.add(preference)
        await self.db.commit()
        await self.db.refresh(preference)
        return preference
    
    async def update(
        self, 
        user_id: int, 
        preference_data: UserPreferenceUpdate
    ) -> Optional[UserPreference]:
        """Update existing user preference"""
        preference = await self.get_by_user_id(user_id)
        if not preference:
            return None
        
        update_data = preference_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preference, field, value)
        
        await self.db.commit()
        await self.db.refresh(preference)
        return preference
    
    async def upsert(
        self, 
        user_id: int, 
        preference_data: UserPreferenceCreate
    ) -> UserPreference:
        """Create or update user preference"""
        existing = await self.get_by_user_id(user_id)
        
        if existing:
            # Update existing
            update_data = preference_data.model_dump()
            for field, value in update_data.items():
                if field != 'user_id':  # Don't update user_id
                    setattr(existing, field, value)
            
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        else:
            # Create new
            return await self.create(preference_data)
    
    async def delete(self, user_id: int) -> bool:
        """Delete user preference"""
        preference = await self.get_by_user_id(user_id)
        if not preference:
            return False
        
        await self.db.delete(preference)
        await self.db.commit()
        return True
