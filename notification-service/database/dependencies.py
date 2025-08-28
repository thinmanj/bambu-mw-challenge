from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_database_session
from core.services import (
    NotificationTemplateService,
    NotificationLogService,
    UserPreferenceService,
    NotificationService,
)


# Database dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database dependency for FastAPI"""
    async for db in get_database_session():
        yield db


# Service dependencies
async def get_notification_template_service(
    db: AsyncSession = Depends(get_db)
) -> NotificationTemplateService:
    """Get notification template service"""
    return NotificationTemplateService(db)


async def get_notification_log_service(
    db: AsyncSession = Depends(get_db)
) -> NotificationLogService:
    """Get notification log service"""
    return NotificationLogService(db)


async def get_user_preference_service(
    db: AsyncSession = Depends(get_db)
) -> UserPreferenceService:
    """Get user preference service"""
    return UserPreferenceService(db)


async def get_notification_service(
    db: AsyncSession = Depends(get_db)
) -> NotificationService:
    """Get notification service with database session"""
    return NotificationService(db)
