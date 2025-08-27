import os
import logging
import traceback
from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, time
from enum import Enum
import uvicorn

# Define enums locally for demo (to avoid SQLAlchemy dependencies)
class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"

# Define Pydantic models for demo (following api.v1.schemas structure)
class BaseSchema(BaseModel):
    model_config = {"from_attributes": True}

class NotificationRequest(BaseModel):
    user_id: int = Field(..., description="User ID who will receive the notification")
    template_name: str = Field(..., description="Name of the notification template to use")
    context: Dict[str, Any] = Field(..., description="Template variables/context for rendering")

class NotificationResponse(BaseModel):
    id: int
    status: NotificationStatus
    message: str
    created_at: datetime

class NotificationTemplateBase(BaseModel):
    name: str = Field(..., max_length=100, description="Template name")
    subject: Optional[str] = Field(None, max_length=255, description="Template subject")
    body: str = Field(..., description="Template body content")
    type: NotificationType = Field(..., description="Notification type")
    variables: Optional[Dict[str, Any]] = Field(None, description="Template variables")

class NotificationTemplateCreate(NotificationTemplateBase):
    pass

class NotificationTemplate(NotificationTemplateBase, BaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime

class NotificationLogUpdate(BaseModel):
    status: Optional[NotificationStatus] = Field(None, description="Notification status")
    sent_at: Optional[datetime] = Field(None, description="When notification was sent")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class NotificationLogBase(BaseModel):
    user_id: int = Field(..., description="User ID")
    template_id: Optional[int] = Field(None, description="Template ID")
    type: NotificationType = Field(..., description="Notification type")
    status: NotificationStatus = Field(NotificationStatus.PENDING, description="Notification status")
    sent_at: Optional[datetime] = Field(None, description="When notification was sent")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class NotificationLog(NotificationLogBase, BaseSchema):
    id: int
    created_at: datetime
    template: Optional[NotificationTemplate] = None

class UserPreferenceBase(BaseModel):
    user_id: int = Field(..., description="User ID")
    email_enabled: bool = Field(True, description="Email notifications enabled")
    sms_enabled: bool = Field(True, description="SMS notifications enabled")
    push_enabled: bool = Field(True, description="Push notifications enabled")
    quiet_hours_start: Optional[time] = Field(None, description="Quiet hours start time")
    quiet_hours_end: Optional[time] = Field(None, description="Quiet hours end time")

class UserPreference(UserPreferenceBase, BaseSchema):
    id: int
    created_at: datetime
    updated_at: datetime

class PaginatedResponse(BaseModel):
    total: int
    page: int = 1
    size: int = 50
    pages: int

class NotificationTemplateList(PaginatedResponse):
    items: List[NotificationTemplate]

class NotificationLogList(PaginatedResponse):
    items: List[NotificationLog]


# Configure logging
def setup_logging():
    """Setup comprehensive logging configuration"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("notification_service.log")
        ]
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Bambu Notification Service (Demo)",
    description="Microservice for handling notifications (email, SMS, push) - Demo Mode",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "notifications",
            "description": "Notification management operations",
        },
        {
            "name": "templates",
            "description": "Template management operations",
        },
        {
            "name": "preferences",
            "description": "User preference management operations",
        },
    ],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data for demo
mock_templates = [
    {
        "id": 1,
        "name": "welcome_email",
        "subject": "Welcome to {app_name}",
        "body": "Hello {user_name}, welcome to our platform!",
        "type": "email",
        "variables": {"app_name": "string", "user_name": "string"},
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
]

# Mock notification logs with proper NotificationLog structure
mock_notifications = [
    {
        "id": 1,
        "user_id": 123,
        "template_id": 1,
        "type": "email",
        "status": "sent",
        "sent_at": datetime.now(),
        "error_message": None,
        "metadata": {"provider": "sendgrid", "message_id": "sg_123456"},
        "created_at": datetime.now(),
        "template": None  # We'll keep this simple for demo
    }
]
mock_preferences = {}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "notification-service",
        "version": "1.0.0",
        "status": "running",
        "mode": "demo",
        "api_versions": ["v1"],
        "api_base_url": "/api/v1"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "notification-service",
        "mode": "demo",
        "database": "mock",
        "cache": "mock"
    }

# API v1 endpoints

# Notifications Management
@app.post("/api/v1/notifications/send", response_model=NotificationResponse, tags=["notifications"])
async def send_notification(request: NotificationRequest):
    """Send a notification"""
    logger.info(f"🚀 Sending notification - user_id: {request.user_id}, template: {request.template_name}")
    
    try:
        # Find the template by name
        template_found = None
        template_id = None
        template_type = NotificationType.EMAIL  # Default
        
        for template in mock_templates:
            if template["name"] == request.template_name:
                template_found = template
                template_id = template["id"]
                template_type = NotificationType(template["type"])
                logger.info(f"✅ Template found - id: {template_id}, type: {template_type}")
                break
        
        if not template_found:
            logger.error(f"❌ Template not found - name: {request.template_name}")
            raise HTTPException(status_code=404, detail=f"Template '{request.template_name}' not found")
        
        # Create notification log entry
        notification_log = {
            "id": len(mock_notifications) + 1,
            "user_id": request.user_id,
            "template_id": template_id,
            "type": template_type.value,
            "status": NotificationStatus.PENDING.value,
            "sent_at": None,
            "error_message": None,
            "metadata": {
                "template_name": request.template_name,
                "context": request.context,
                "rendered_subject": template_found.get("subject", ""),
                "rendered_body": template_found.get("body", "")
            },
            "created_at": datetime.now(),
            "template": None
        }
        mock_notifications.append(notification_log)
        
        logger.info(f"✅ Notification created successfully - id: {notification_log['id']}, user_id: {request.user_id}")
        
        # Return simplified response for the send operation
        return NotificationResponse(
            id=notification_log["id"],
            status=NotificationStatus.PENDING,
            message=f"Notification queued for user {request.user_id} using template '{request.template_name}'",
            created_at=notification_log["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Unexpected error sending notification - user_id: {request.user_id}, error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while sending notification")

@app.get("/api/v1/notifications/{id}", response_model=NotificationLog, tags=["notifications"])
async def get_notification_details(id: int = Path(..., description="Notification ID")):
    """Get notification details"""
    logger.info(f"🔍 Getting notification details - id: {id}")
    
    for notif in mock_notifications:
        if notif["id"] == id:
            logger.info(f"✅ Notification found - id: {id}")
            return NotificationLog(**notif)
    
    logger.warning(f"⚠️ Notification not found - id: {id}")
    raise HTTPException(status_code=404, detail="Notification not found")

@app.get("/api/v1/notifications/user/{user_id}", response_model=NotificationLogList, tags=["notifications"])
async def list_user_notifications(
    user_id: int = Path(..., description="User ID"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size")
):
    """List user notifications"""
    user_notifications = [n for n in mock_notifications if n.get("user_id") == user_id]
    notification_logs = [NotificationLog(**n) for n in user_notifications]
    
    return NotificationLogList(
        items=notification_logs,
        total=len(notification_logs),
        page=page,
        size=size,
        pages=(len(notification_logs) + size - 1) // size  # Calculate total pages
    )

@app.put("/api/v1/notifications/{id}/status", response_model=NotificationLog, tags=["notifications"])
async def update_notification_status(
    update_data: NotificationLogUpdate,
    id: int = Path(..., description="Notification ID")
):
    """Update notification status"""
    for i, notification in enumerate(mock_notifications):
        if notification["id"] == id:
            # Update only provided fields
            update_dict = update_data.model_dump(exclude_unset=True)
            mock_notifications[i].update(update_dict)
            mock_notifications[i]["updated_at"] = datetime.now()
            return NotificationLog(**mock_notifications[i])
    raise HTTPException(status_code=404, detail="Notification not found")

# Template Management
@app.get("/api/v1/templates", response_model=NotificationTemplateList, tags=["templates"])
async def list_templates(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    type_filter: Optional[str] = Query(None, description="Filter by notification type")
):
    """List all templates"""
    try:
        logger.info(f"📋 Listing templates - page: {page}, size: {size}, filter: {type_filter}")
        
        filtered = mock_templates
        if type_filter:
            filtered = [t for t in mock_templates if t["type"] == type_filter]
            logger.info(f"🔍 Applied type filter '{type_filter}' - {len(filtered)} templates found")
        
        logger.info(f"✅ Templates retrieved - total: {len(filtered)}")
        
        return NotificationTemplateList(
            items=filtered,
            total=len(filtered),
            page=page,
            size=size,
            pages=1
        )
    except Exception as e:
        logger.error(f"💥 Error listing templates - error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while listing templates")

@app.post("/api/v1/templates", response_model=NotificationTemplate, status_code=201, tags=["templates"])
async def create_template(template_data: NotificationTemplateCreate):
    """Create new template"""
    try:
        logger.info(f"📝 Creating template - name: {template_data.name}, type: {template_data.type}")
        
        template = {
            "id": len(mock_templates) + 1,
            **template_data.model_dump(),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        mock_templates.append(template)
        
        logger.info(f"✅ Template created successfully - id: {template['id']}, name: {template['name']}")
        
        return NotificationTemplate(**template)
    except Exception as e:
        logger.error(f"💥 Error creating template - name: {template_data.name}, error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while creating template")

@app.get("/api/v1/templates/{id}", response_model=NotificationTemplate, tags=["templates"])
async def get_template_details(id: int = Path(..., description="Template ID")):
    """Get template details"""
    for template in mock_templates:
        if template["id"] == id:
            return NotificationTemplate(**template)
    raise HTTPException(status_code=404, detail="Template not found")

@app.put("/api/v1/templates/{id}", response_model=NotificationTemplate, tags=["templates"])
async def update_template(
    template_data: dict,
    id: int = Path(..., description="Template ID")
):
    """Update template"""
    for i, template in enumerate(mock_templates):
        if template["id"] == id:
            mock_templates[i].update(template_data)
            mock_templates[i]["updated_at"] = datetime.now()
            return NotificationTemplate(**mock_templates[i])
    raise HTTPException(status_code=404, detail="Template not found")

@app.delete("/api/v1/templates/{id}", status_code=204, tags=["templates"])
async def delete_template(id: int = Path(..., description="Template ID")):
    """Delete template"""
    for i, template in enumerate(mock_templates):
        if template["id"] == id:
            mock_templates.pop(i)
            return
    raise HTTPException(status_code=404, detail="Template not found")

# User Preferences
@app.get("/api/v1/preferences/user/{user_id}", response_model=UserPreference, tags=["preferences"])
async def get_user_preferences(user_id: int = Path(..., description="User ID")):
    """Get user preferences"""
    logger.info(f"📊 Getting user preferences - user_id: {user_id}")
    
    if user_id not in mock_preferences:
        logger.info(f"🆕 Creating default preferences for user - user_id: {user_id}")
        # Create default preferences
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
    
    logger.info(f"✅ User preferences retrieved - user_id: {user_id}")
    return UserPreference(**mock_preferences[user_id])

@app.put("/api/v1/preferences/user/{user_id}", response_model=UserPreference, tags=["preferences"])
async def update_user_preferences(
    preference_data: dict,
    user_id: int = Path(..., description="User ID")
):
    """Update user preferences"""
    logger.info(f"🔧 Updating user preferences - user_id: {user_id}, data: {preference_data}")
    
    try:
        if user_id not in mock_preferences:
            logger.info(f"🆕 Creating default preferences before update - user_id: {user_id}")
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
        
        mock_preferences[user_id].update(preference_data)
        mock_preferences[user_id]["updated_at"] = datetime.now()
        
        logger.info(f"✅ User preferences updated successfully - user_id: {user_id}")
        
        return UserPreference(**mock_preferences[user_id])
        
    except Exception as e:
        logger.error(f"💥 Error updating user preferences - user_id: {user_id}, error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error while updating user preferences")

# Version endpoint
@app.get("/api/v1/version", tags=["v1"])
async def get_version():
    """Get API version information"""
    return {
        "version": "1.0.0",
        "api_version": "v1",
        "mode": "demo",
        "notification_management": [
            "POST /api/v1/notifications/send",
            "GET /api/v1/notifications/{id}",
            "GET /api/v1/notifications/user/{user_id}",
            "PUT /api/v1/notifications/{id}/status",
        ],
        "template_management": [
            "GET /api/v1/templates",
            "POST /api/v1/templates",
            "GET /api/v1/templates/{id}",
            "PUT /api/v1/templates/{id}",
            "DELETE /api/v1/templates/{id}",
        ],
        "user_preferences": [
            "GET /api/v1/preferences/user/{user_id}",
            "PUT /api/v1/preferences/user/{user_id}",
        ]
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    print(f"🚀 Starting Notification Service Demo on http://localhost:{port}")
    print(f"📚 API Documentation: http://localhost:{port}/docs")
    print(f"📋 API Endpoints: http://localhost:{port}/api/v1/version")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
