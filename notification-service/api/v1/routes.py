from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import Optional
import logging
import traceback
from api.v1.schemas import (
    NotificationRequest, NotificationResponse, SendNotificationResponse,
    NotificationTemplateCreate, NotificationTemplateUpdate, NotificationTemplate,
    NotificationTemplateList, NotificationLogCreate, NotificationLogUpdate,
    NotificationLog, NotificationLogList, UserPreferenceCreate,
    UserPreferenceUpdate, UserPreference
)
from core.services import (
    NotificationService, NotificationTemplateService,
    NotificationLogService, UserPreferenceService
)
from database.dependencies import (
    get_notification_service, get_notification_template_service,
    get_notification_log_service, get_user_preference_service
)

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("notification_service.log")
    ]
)

logger = logging.getLogger(__name__)

# Notifications Management Router
notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])

@notifications_router.post("/send", response_model=SendNotificationResponse)
async def send_notification(
    request: NotificationRequest,
    service: NotificationService = Depends(get_notification_service)
):
    """Send a notification using a template"""
    logger.info(f"📤 Sending notification - user_id: {request.user_id}, template: {request.template_name}")
    try:
        result = await service.send_notification(
            user_id=request.user_id,
            template_name=request.template_name,
            context=request.context
        )
        
        status_code = 200 if result["success"] else 400
        
        response = SendNotificationResponse(
            success=result["success"],
            notification_id=result.get("notification_id"),
            error=result.get("error"),
            type=result.get("type"),
            template_name=result.get("template_name"),
            skipped=result.get("skipped", False),
            message=f"Notification {'sent' if result['success'] else 'failed'}" if not result.get("skipped") else "Notification skipped due to user preferences"
        )
        
        if result["success"]:
            logger.info(f"✅ Notification sent successfully - id: {result.get('notification_id')}, user_id: {request.user_id}")
        elif result.get("skipped"):
            logger.info(f"⏭️ Notification skipped - id: {result.get('notification_id')}, user_id: {request.user_id}")
        else:
            logger.error(f"❌ Notification failed - id: {result.get('notification_id')}, user_id: {request.user_id}, error: {result.get('error')}")
        
        return response
        
    except Exception as e:
        logger.error(f"💥 Failed to send notification - user_id: {request.user_id}, template: {request.template_name}, error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@notifications_router.get("/{id}", response_model=NotificationLog)
async def get_notification_details(
    id: int = Path(..., description="Notification ID"),
    service: NotificationLogService = Depends(get_notification_log_service)
):
    """Get notification details"""
    logger.info(f" Getting notification details - id: {id}")
    try:
        notification = await service.get_log(id)
        if not notification:
            logger.warning(f" Notification not found - id: {id}")
            raise HTTPException(status_code=404, detail="Notification not found")
        logger.info(f" Notification retrieved - id: {id}, user_id: {notification.user_id}")
        return notification
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f" Error getting notification details - id: {id}, error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")

@notifications_router.get("/user/{user_id}", response_model=NotificationLogList)
async def list_user_notifications(
    user_id: int = Path(..., description="User ID"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    service: NotificationLogService = Depends(get_notification_log_service)
):
    """List user notifications"""
    return await service.get_user_logs(user_id, page, size)

@notifications_router.put("/{id}/status", response_model=NotificationLog)
async def update_notification_status(
    update_data: NotificationLogUpdate,
    id: int = Path(..., description="Notification ID"),
    service: NotificationLogService = Depends(get_notification_log_service)
):
    """Update notification status"""
    notification = await service.update_log(id, update_data)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification


# Template Management Router
templates_router = APIRouter(prefix="/templates", tags=["templates"])

@templates_router.get("/", response_model=NotificationTemplateList)
async def list_templates(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    type_filter: Optional[str] = Query(None, description="Filter by notification type"),
    service: NotificationTemplateService = Depends(get_notification_template_service)
):
    """List all templates"""
    logger.info(f" Listing templates - page: {page}, size: {size}, filter: {type_filter}")
    try:
        result = await service.list_templates(page, size, type_filter)
        logger.info(f" Templates retrieved - total: {result.total}")
        return result
    except Exception as e:
        logger.error(f" Error listing templates - error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error")

@templates_router.post("/", response_model=NotificationTemplate, status_code=201)
async def create_template(
    template_data: NotificationTemplateCreate,
    service: NotificationTemplateService = Depends(get_notification_template_service)
):
    """Create new template"""
    logger.info(f" Creating template - name: {template_data.name}, type: {template_data.type}")
    try:
        result = await service.create_template(template_data)
        logger.info(f" Template created successfully - id: {result.id}, name: {result.name}")
        return result
    except Exception as e:
        # Handle unique constraint violations
        if "unique" in str(e).lower():
            logger.error(f" Template name conflict - name: {template_data.name}")
            raise HTTPException(status_code=400, detail="Template name already exists")
        logger.error(f" Error creating template - name: {template_data.name}, error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@templates_router.get("/{id}", response_model=NotificationTemplate)
async def get_template_details(
    id: int = Path(..., description="Template ID"),
    service: NotificationTemplateService = Depends(get_notification_template_service)
):
    """Get template details"""
    template = await service.get_template(id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@templates_router.put("/{id}", response_model=NotificationTemplate)
async def update_template(
    template_data: NotificationTemplateUpdate,
    id: int = Path(..., description="Template ID"),
    service: NotificationTemplateService = Depends(get_notification_template_service)
):
    """Update template"""
    template = await service.update_template(id, template_data)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@templates_router.delete("/{id}", status_code=204)
async def delete_template(
    id: int = Path(..., description="Template ID"),
    service: NotificationTemplateService = Depends(get_notification_template_service)
):
    """Delete template"""
    success = await service.delete_template(id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")


# User Preferences Router
preferences_router = APIRouter(prefix="/preferences", tags=["preferences"])

@preferences_router.get("/user/{user_id}", response_model=UserPreference)
async def get_user_preferences(
    user_id: int = Path(..., description="User ID"),
    service: UserPreferenceService = Depends(get_user_preference_service)
):
    """Get user preferences"""
    preferences = await service.get_user_preference(user_id)
    if not preferences:
        # Create default preferences if they don't exist
        default_preferences = UserPreferenceCreate(user_id=user_id)
        preferences = await service.create_user_preference(default_preferences)
    return preferences

@preferences_router.put("/user/{user_id}", response_model=UserPreference)
async def update_user_preferences(
    preference_data: UserPreferenceUpdate,
    user_id: int = Path(..., description="User ID"),
    service: UserPreferenceService = Depends(get_user_preference_service)
):
    """Update user preferences"""
    # Use upsert to create if doesn't exist or update if exists
    create_data = UserPreferenceCreate(
        user_id=user_id,
        **preference_data.model_dump(exclude_unset=True)
    )
    return await service.upsert_user_preference(user_id, create_data)
