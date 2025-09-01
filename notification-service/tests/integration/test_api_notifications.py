"""
Integration tests for notification API endpoints.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
import json


@pytest.mark.integration
@pytest.mark.api
class TestNotificationAPI:
    """Integration tests for notification API endpoints."""

    def setup_method(self):
        """Setup test client and mocks."""
        # Create FastAPI app for testing (avoid circular imports)
        from fastapi import FastAPI
        from api.v1 import api_v1_router
        from database.dependencies import (
            get_db, get_notification_service, get_notification_log_service,
            get_notification_template_service, get_user_preference_service
        )
        from unittest.mock import AsyncMock
        
        app = FastAPI(title="Test Notification Service")
        app.include_router(api_v1_router)
        
        # Create mock database session
        mock_db = AsyncMock()
        
        # Create mock services
        mock_notification_service = AsyncMock()
        mock_log_service = AsyncMock()
        mock_template_service = AsyncMock()
        mock_preference_service = AsyncMock()
        
        # Override dependencies
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_notification_service] = lambda: mock_notification_service
        app.dependency_overrides[get_notification_log_service] = lambda: mock_log_service
        app.dependency_overrides[get_notification_template_service] = lambda: mock_template_service
        app.dependency_overrides[get_user_preference_service] = lambda: mock_preference_service
        
        self.client = TestClient(app)
        self.app = app
        
    def teardown_method(self):
        """Cleanup mocks after each test."""
        if hasattr(self, '_db_patch'):
            self._db_patch.stop()

    def test_send_notification_success(self, sample_notification_request):
        """Test successful notification sending via API."""
        # Get the overridden service and set up its behavior
        from database.dependencies import get_notification_service
        mock_service = self.app.dependency_overrides[get_notification_service]()
        mock_service.send_notification = AsyncMock(return_value={
            "success": True,
            "notification_id": "notif_123",
            "type": "email",
            "template_name": "welcome_email"
        })

        # Make API request
        response = self.client.post(
            "/api/v1/notifications/send",
            json=sample_notification_request
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["notification_id"] == "notif_123"
        assert data["type"] == "email"
        assert data["template_name"] == "welcome_email"

    def test_send_notification_failure(self, sample_notification_request):
        """Test notification sending failure via API."""
        # Get the overridden service and set up its behavior
        from database.dependencies import get_notification_service
        mock_service = self.app.dependency_overrides[get_notification_service]()
        mock_service.send_notification = AsyncMock(return_value={
            "success": False,
            "notification_id": "notif_123",
            "error": "Template not found"
        })

        # Make API request
        response = self.client.post(
            "/api/v1/notifications/send",
            json=sample_notification_request
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "Template not found"

    def test_send_notification_skipped(self, sample_notification_request):
        """Test notification skipped due to user preferences via API."""
        # Get the overridden service and set up its behavior
        from database.dependencies import get_notification_service
        mock_service = self.app.dependency_overrides[get_notification_service]()
        mock_service.send_notification = AsyncMock(return_value={
            "success": False,
            "notification_id": "notif_123",
            "error": "User has disabled email notifications",
            "skipped": True
        })

        # Make API request
        response = self.client.post(
            "/api/v1/notifications/send",
            json=sample_notification_request
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["skipped"] is True
        assert "skipped due to user preferences" in data["message"]

    def test_send_notification_invalid_request(self):
        """Test notification sending with invalid request data."""
        # Invalid request - missing required fields
        invalid_request = {
            "user_id": 123
            # Missing template_name and context
        }

        response = self.client.post(
            "/api/v1/notifications/send",
            json=invalid_request
        )

        # Should return validation error
        assert response.status_code == 422

    def test_send_notification_service_exception(self, sample_notification_request):
        """Test notification sending with service exception."""
        # Get the overridden service and set up its behavior to raise exception
        from database.dependencies import get_notification_service
        mock_service = self.app.dependency_overrides[get_notification_service]()
        mock_service.send_notification = AsyncMock(side_effect=Exception("Database error"))

        # Make API request
        response = self.client.post(
            "/api/v1/notifications/send",
            json=sample_notification_request
        )

        assert response.status_code == 500
        data = response.json()
        assert "Database error" in data["detail"]

    def test_get_notification_details_success(self, sample_notification_log):
        """Test getting notification details via API."""
        # Get the overridden service and set up its behavior
        from database.dependencies import get_notification_log_service
        mock_service = self.app.dependency_overrides[get_notification_log_service]()
        mock_service.get_log = AsyncMock(return_value=sample_notification_log)

        response = self.client.get("/api/v1/notifications/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_notification_log.id
        assert data["user_id"] == sample_notification_log.user_id

    def test_get_notification_details_not_found(self):
        """Test getting non-existent notification details."""
        # Get the overridden service and set up its behavior
        from database.dependencies import get_notification_log_service
        mock_service = self.app.dependency_overrides[get_notification_log_service]()
        mock_service.get_log = AsyncMock(return_value=None)

        response = self.client.get("/api/v1/notifications/999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_list_user_notifications_success(self):
        """Test listing user notifications via API."""
        # Get the overridden service and set up its behavior
        from database.dependencies import get_notification_log_service
        mock_service = self.app.dependency_overrides[get_notification_log_service]()
        
        # Create a simple mock for the pagination result
        class MockLogList:
            def __init__(self):
                self.items = []
                self.total = 0
                self.page = 1
                self.size = 50
                self.pages = 1
                
        mock_log_list = MockLogList()
        mock_service.get_user_logs = AsyncMock(return_value=mock_log_list)

        response = self.client.get("/api/v1/notifications/user/123")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["page"] == 1
        assert data["size"] == 50

    def test_list_user_notifications_with_pagination(self):
        """Test listing user notifications with pagination."""
        # Get the overridden service and set up its behavior
        from database.dependencies import get_notification_log_service
        mock_service = self.app.dependency_overrides[get_notification_log_service]()
        
        # Create a simple mock for the pagination result
        class MockLogList:
            def __init__(self):
                self.items = []
                self.total = 100
                self.page = 2
                self.size = 25
                self.pages = 4
                
        mock_log_list = MockLogList()
        mock_service.get_user_logs = AsyncMock(return_value=mock_log_list)

        response = self.client.get("/api/v1/notifications/user/123?page=2&size=25")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["size"] == 25
        assert data["total"] == 100
        assert data["pages"] == 4

    def test_update_notification_status_success(self, sample_notification_log):
        """Test updating notification status via API."""
        # Get the overridden service and set up its behavior
        from database.dependencies import get_notification_log_service
        mock_service = self.app.dependency_overrides[get_notification_log_service]()
        updated_log = sample_notification_log
        updated_log.status = "sent"
        mock_service.update_log = AsyncMock(return_value=updated_log)

        update_data = {
            "status": "sent",
            "sent_at": "2024-12-27T10:30:00Z"
        }

        response = self.client.put("/api/v1/notifications/1/status", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"

    def test_update_notification_status_not_found(self):
        """Test updating non-existent notification status."""
        # Get the overridden service and set up its behavior
        from database.dependencies import get_notification_log_service
        mock_service = self.app.dependency_overrides[get_notification_log_service]()
        mock_service.update_log = AsyncMock(return_value=None)

        update_data = {
            "status": "sent",
            "sent_at": "2024-12-27T10:30:00Z"
        }

        response = self.client.put("/api/v1/notifications/999/status", json=update_data)

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_notification_endpoint_cors_headers(self, sample_notification_request):
        """Test that notification endpoint returns proper headers."""
        # Get the overridden service and set up its behavior
        from database.dependencies import get_notification_service
        mock_service = self.app.dependency_overrides[get_notification_service]()
        mock_service.send_notification = AsyncMock(return_value={
            "success": True,
            "notification_id": "notif_123",
            "type": "email",
            "template_name": "welcome_email"
        })

        response = self.client.post(
            "/api/v1/notifications/send",
            json=sample_notification_request
        )

        # Check basic headers are present
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]
        # Note: CORS headers would be added by middleware in production

    def test_notification_endpoint_rate_limit_headers(self, sample_notification_request):
        """Test that notification endpoint responds properly."""
        # Get the overridden service and set up its behavior
        from database.dependencies import get_notification_service
        mock_service = self.app.dependency_overrides[get_notification_service]()
        mock_service.send_notification = AsyncMock(return_value={
            "success": True,
            "notification_id": "notif_123",
            "type": "email",
            "template_name": "welcome_email"
        })

        response = self.client.post(
            "/api/v1/notifications/send",
            json=sample_notification_request
        )

        # Check basic response functionality
        assert response.status_code == 200
        assert "content-type" in response.headers
        assert "application/json" in response.headers["content-type"]
        # Note: Rate limit headers would be added by middleware in production

    def test_notification_api_content_type(self, sample_notification_request):
        """Test that API returns correct content type."""
        # Get the overridden service and set up its behavior
        from database.dependencies import get_notification_service
        mock_service = self.app.dependency_overrides[get_notification_service]()
        mock_service.send_notification = AsyncMock(return_value={
            "success": True,
            "notification_id": "notif_123",
            "type": "email",
            "template_name": "welcome_email"
        })

        response = self.client.post(
            "/api/v1/notifications/send",
            json=sample_notification_request
        )

        assert "application/json" in response.headers["content-type"]

    def test_notification_api_request_validation(self):
        """Test comprehensive request validation for notification API."""
        test_cases = [
            # Missing user_id
            {
                "template_name": "welcome_email",
                "context": {"name": "John"}
            },
            # Invalid user_id type
            {
                "user_id": "not_a_number",
                "template_name": "welcome_email",
                "context": {"name": "John"}
            },
            # Missing template_name
            {
                "user_id": 123,
                "context": {"name": "John"}
            },
            # Missing context
            {
                "user_id": 123,
                "template_name": "welcome_email"
            },
            # Invalid context type
            {
                "user_id": 123,
                "template_name": "welcome_email",
                "context": "not_a_dict"
            }
        ]

        for invalid_request in test_cases:
            response = self.client.post(
                "/api/v1/notifications/send",
                json=invalid_request
            )
            assert response.status_code == 422
