# Notification Service API

This microservice provides REST and GraphQL APIs for managing notifications, templates, and user preferences.

## Base URL
```
http://localhost:8003/api/v1
```

## Rate Limiting

The Bambu Notification Service enforces rate limiting to protect the API from abuse and ensure fair usage.

### Rate Limiting Overview

- **Global default limits**: 100 requests per minute, 1000 requests per hour
- **Endpoint-specific limits**:
  - `/api/v1/notifications/send`: 50 requests per minute, 500 requests per hour
  - `/api/v1/templates`: 30 requests per minute, 300 requests per hour
  - `/api/v1/preferences`: 20 requests per minute, 200 requests per hour
- **No rate limiting on health and docs endpoints:** `/`, `/health`, `/docs`, `/redoc`, `/openapi.json`, `/favicon.ico` are excluded

### Rate Limiting Headers

The service provides the following HTTP response headers to inform clients about their current rate limiting status:

| Header | Description |
| --- | --- |
| `X-RateLimit-Limit` | Total allowed requests in the current window |
| `X-RateLimit-Remaining` | Remaining requests in the current window |
| `X-RateLimit-Reset` | Timestamp when the rate limit window resets |
| `X-RateLimit-Window` | Duration of the rate limit window in seconds |
| `X-RateLimit-Limit-Minute` | Allowed requests per minute |
| `X-RateLimit-Remaining-Minute` | Remaining requests for the current minute |
| `X-RateLimit-Limit-Hour` | Allowed requests per hour |
| `X-RateLimit-Remaining-Hour` | Remaining requests for the current hour |

Clients should respect these headers to avoid hitting rate limits which may result in HTTP 429 (Too Many Requests) responses.

## API Documentation
Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc
- **GraphQL Playground**: http://localhost:8003/graphql

## API Endpoints

### GraphQL API

The service provides a GraphQL API at `/graphql` that allows you to query and mutate notification data.

#### Example GraphQL Queries

```graphql
# Get notification by ID
query {
  notification(id: "123") {
    id
    userId
    status
    sentAt
    templateName
  }
}

# Get user notifications
query {
  userNotifications(userId: 123) {
    id
    status
    sentAt
    templateName
  }
}

# Get template by ID
query {
  template(id: "456") {
    id
    name
    subject
    body
    type
  }
}
```

#### Example GraphQL Mutations

```graphql
# Send a notification
mutation {
  sendNotification(
    userId: 123, 
    templateName: "welcome_email", 
    context: {"user_name": "John Doe", "app_name": "MyBambu"}
  ) {
    id
    status
  }
}

# Update notification status
mutation {
  updateNotificationStatus(
    id: "123", 
    status: "sent", 
    sentAt: "2024-12-27T10:30:00Z"
  ) {
    id
    status
    sentAt
  }
}

# Create template
mutation {
  createTemplate(
    name: "welcome_email", 
    subject: "Welcome to {app_name}", 
    body: "Hello {user_name}, welcome to our platform!", 
    type: "email", 
    variables: {"app_name": "string", "user_name": "string"}
  ) {
    id
    name
  }
}
```

### REST API Endpoints

### Notification Management

#### Send Notification
```http
POST /api/v1/notifications/send
Content-Type: application/json

{
  "user_id": 123,
  "template_name": "welcome_email",
  "context": {
    "user_name": "John Doe",
    "app_name": "MyBambu",
    "order_id": "12345"
  }
}
```

#### Get Notification Details
```http
GET /api/v1/notifications/{id}
```

#### List User Notifications
```http
GET /api/v1/notifications/user/{user_id}?page=1&size=50
```

#### Update Notification Status
```http
PUT /api/v1/notifications/{id}/status
Content-Type: application/json

{
  "status": "sent",
  "sent_at": "2024-12-27T10:30:00Z",
  "error_message": null
}
```

### Template Management

#### List Templates
```http
GET /api/v1/templates?page=1&size=50&type_filter=email
```

#### Create Template
```http
POST /api/v1/templates
Content-Type: application/json

{
  "name": "welcome_email",
  "subject": "Welcome to {app_name}",
  "body": "Hello {user_name}, welcome to our platform!",
  "type": "email",
  "variables": {"app_name": "string", "user_name": "string"}
}
```

#### Get Template Details
```http
GET /api/v1/templates/{id}
```

#### Update Template
```http
PUT /api/v1/templates/{id}
Content-Type: application/json

{
  "subject": "Welcome to {app_name} - Updated",
  "body": "Hello {user_name}, welcome to our amazing platform!"
}
```

#### Delete Template
```http
DELETE /api/v1/templates/{id}
```

### User Preferences

#### Get User Preferences
```http
GET /api/v1/preferences/user/{user_id}
```

#### Update User Preferences
```http
PUT /api/v1/preferences/user/{user_id}
Content-Type: application/json

{
  "email_enabled": true,
  "sms_enabled": false,
  "push_enabled": true,
  "quiet_hours_start": "22:00:00",
  "quiet_hours_end": "08:00:00"
}
```

## Data Models

### Notification Types
- `email` - Email notifications
- `sms` - SMS notifications  
- `push` - Push notifications

### Notification Status
- `pending` - Notification is queued for sending
- `sent` - Notification has been sent
- `failed` - Failed to send notification
- `bounced` - Notification bounced back

## Error Responses

All endpoints return appropriate HTTP status codes:

- `200` - Success
- `201` - Created
- `204` - No Content (for DELETE operations)
- `400` - Bad Request (validation errors)
- `404` - Not Found
- `500` - Internal Server Error

Error response format:
```json
{
  "detail": "Error message describing the issue"
}
```

## Pagination

List endpoints support pagination with query parameters:
- `page` - Page number (default: 1)
- `size` - Items per page (default: 50, max: 100)

Paginated response format:
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "size": 50,
  "pages": 3
}
```

## Getting Started

1. Start the service:
```bash
# Demo version (recommended for testing)
python main_demo.py

# Or production version
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

2. Visit the interactive documentation:
```
http://localhost:8003/docs
```

3. Create your first template:
```bash
curl -X POST "http://localhost:8003/api/v1/templates" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "order_confirmation",
    "subject": "Order Confirmed - #{order_id}",
    "body": "Hello {user_name}, your order {order_id} has been confirmed!",
    "type": "email",
    "variables": {"user_name": "string", "order_id": "string"}
  }'
```

4. Send a notification using the template:
```bash
curl -X POST "http://localhost:8003/api/v1/notifications/send" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "template_name": "order_confirmation",
    "context": {
      "user_name": "John Doe",
      "order_id": "ORD-12345"
    }
  }'
```
