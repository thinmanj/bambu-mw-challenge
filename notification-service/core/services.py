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
    """Enhanced notification service with dynamic adapter loading and template support"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.template_service = NotificationTemplateService(db)
        self.log_service = NotificationLogService(db)
        self.preference_service = UserPreferenceService(db)
        self.adapters = {}
        self._load_adapters()
    
    def _load_adapters(self):
        """Dynamically load all adapters from the adapters directory"""
        import os
        import importlib
        import logging
        
        logger = logging.getLogger(__name__)
        adapters_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'adapters')
        
        if not os.path.exists(adapters_dir):
            logger.warning(f"⚠️ Adapters directory not found: {adapters_dir}")
            return
        
        logger.info(f"🔍 Loading adapters from: {adapters_dir}")
        
        for filename in os.listdir(adapters_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                adapter_name = filename[:-3]  # Remove .py extension
                
                try:
                    # Import the module
                    module = importlib.import_module(f'adapters.{adapter_name}')
                    
                    # Look for a class with 'Provider' in the name
                    provider_class = None
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            'provider' in attr_name.lower() and 
                            hasattr(attr, 'send')):
                            provider_class = attr
                            break
                    
                    if provider_class:
                        # Initialize the provider
                        provider_instance = provider_class()
                        self.adapters[adapter_name] = provider_instance
                        logger.info(f"✅ Loaded {adapter_name} adapter: {provider_class.__name__}")
                    else:
                        logger.warning(f"⚠️ No provider class found in {adapter_name}.py")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to load {adapter_name} adapter: {e}")
        
        logger.info(f"📦 Loaded {len(self.adapters)} adapters: {list(self.adapters.keys())}")
    
    def _render_template(self, template_content: str, context: Dict[str, Any]) -> str:
        """Simple template rendering using string formatting"""
        try:
            # Simple variable substitution using {variable_name} format
            return template_content.format(**context)
        except KeyError as e:
            # If a variable is missing, leave it as is and log a warning
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"⚠️ Template variable not found in context: {e}")
            return template_content
    
    async def send_notification(
        self, 
        user_id: int, 
        template_name: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a notification using template and context"""
        import logging
        logger = logging.getLogger(__name__)
        
        notification_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        try:
            # Get the notification template
            template = await self.template_service.get_template_by_name(template_name)
            if not template:
                error_msg = f"Template '{template_name}' not found"
                logger.error(f"❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "notification_id": notification_id
                }
            
            # Check user preferences (optional - don't block if missing)
            user_prefs = await self.preference_service.get_user_preference(user_id)
            if user_prefs:
                # Check if user has disabled this type of notification
                notification_enabled = getattr(user_prefs, f"{template.type}_enabled", True)
                if not notification_enabled:
                    logger.info(f"⏭️ User {user_id} has disabled {template.type} notifications")
                    return {
                        "success": False,
                        "error": f"User has disabled {template.type} notifications",
                        "notification_id": notification_id,
                        "skipped": True
                    }
            
            # Get the appropriate adapter
            adapter = self.adapters.get(template.type)
            if not adapter:
                error_msg = f"No adapter found for type '{template.type}'"
                logger.error(f"❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "notification_id": notification_id
                }
            
            # Render template content
            rendered_subject = self._render_template(template.subject, context)
            rendered_body = self._render_template(template.body, context)
            
            # Prepare adapter context with rendered content
            adapter_context = {
                **context,  # Original context
                'subject': rendered_subject,
                'body': rendered_body,
                'message': rendered_body,  # Alias for SMS/Push
                'title': rendered_subject,  # Alias for Push notifications
            }
            
            # Log the notification attempt
            log_data = NotificationLogCreate(
                id=notification_id,
                user_id=user_id,
                template_name=template_name,
                notification_type=template.type,
                status=NotificationStatus.PENDING,
                created_at=created_at
            )
            notification_log = await self.log_service.create_log(log_data)
            
            # Send using the adapter
            logger.info(f"📤 Sending {template.type} notification to user {user_id} using template '{template_name}'")
            result = adapter.send(adapter_context)
            
            # Update the log based on result
            if result.get('success'):
                await self.log_service.update_log(
                    notification_log.id,
                    NotificationLogUpdate(
                        status=NotificationStatus.SENT,
                        sent_at=datetime.utcnow(),
                        response_data=result
                    )
                )
                
                logger.info(f"✅ Successfully sent {template.type} notification {notification_id}")
                return {
                    "success": True,
                    "notification_id": notification_id,
                    "type": template.type,
                    "template_name": template_name,
                    "adapter_result": result
                }
            else:
                await self.log_service.update_log(
                    notification_log.id,
                    NotificationLogUpdate(
                        status=NotificationStatus.FAILED,
                        error_message=result.get('error', 'Unknown error'),
                        response_data=result
                    )
                )
                
                logger.error(f"❌ Failed to send {template.type} notification {notification_id}: {result.get('error')}")
                return {
                    "success": False,
                    "notification_id": notification_id,
                    "error": result.get('error'),
                    "adapter_result": result
                }
                
        except Exception as e:
            logger.error(f"💥 Unexpected error sending notification {notification_id}: {e}")
            
            # Try to update log if it was created
            try:
                await self.log_service.update_log(
                    notification_id,
                    NotificationLogUpdate(
                        status=NotificationStatus.FAILED,
                        error_message=str(e)
                    )
                )
            except:
                pass  # Log update failed, but don't mask the original error
            
            return {
                "success": False,
                "notification_id": notification_id,
                "error": str(e)
            }
