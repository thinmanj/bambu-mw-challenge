# Notification Service API

This microservice provides REST and GraphQL APIs for managing notifications, templates, and user preferences.

## Base URL
```
http://localhost:8001/api/v1
```

## Rate Limiting

The Bambu Notification Service enforces rate limiting to protect the API from abuse and ensure fair usage.

### Rate Limiting Overview

- **Global default limits**: 100 requests per minute, 1000 requests per hour
- **Endpoint-specific limits**:
  - `/api/v1/notifications/send`: 50 requests per minute, 500 requests per hour
  - `/api/v1/templates`: 30 requests per minute, 300 requests per hour
  - `/api/v1/preferences`: 20 requests per minute, 200 requests per hour
- **No rate limiting on health and docs endpoints:** `/`, `/health`, `/health/live`, `/health/ready`, `/health/startup`, `/docs`, `/redoc`, `/openapi.json`, `/favicon.ico` are excluded

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

## Health Check Endpoints

The service provides multiple health check endpoints designed for different monitoring and orchestration needs:

### Kubernetes Health Probes

#### Liveness Probe
```http
GET /health/live
```
Indicates if the service process is running. Returns 200 if the service is alive.
Kubernetes will restart the pod if this fails.

#### Readiness Probe
```http
GET /health/ready
```
Indicates if the service is ready to accept requests. Performs dependency checks (database, Redis).
Kubernetes will not route traffic to the pod if this fails.

#### Startup Probe
```http
GET /health/startup
```
Indicates if the service has completed initialization.
Kubernetes will not perform liveness/readiness checks until this succeeds.

#### Legacy Health Check
```http
GET /health
```
Backward-compatible health check endpoint that combines basic liveness and readiness information.

#### BulkheadExecutor Health Check
```http
GET /health/bulkhead
```
Provides detailed health information about the BulkheadExecutor resilience system, including per-partition metrics and overall status for monitoring notification channel health.

## Resilience & Retry Features

The notification service includes comprehensive resilience features to ensure reliable delivery:

### Automatic Retry with Exponential Backoff

All notification adapters (Email, SMS, Push) automatically retry failed requests using the [Tenacity](https://tenacity.readthedocs.io/) library:

- **Exponential Backoff**: Delays between retries grow exponentially (1s, 2s, 4s, ...)
- **Smart Error Classification**: Distinguishes between retryable and non-retryable errors
- **Configurable**: Maximum attempts (default: 3), backoff factor (default: 2x), max delay (default: 30s)

**Example retry sequence:**
```
2024-12-27 10:30:01 [INFO] Attempting email send to user@example.com
2024-12-27 10:30:01 [WARN] Email send failed: API timeout - retrying in 1s
2024-12-27 10:30:02 [WARN] Email send failed: API timeout - retrying in 2s  
2024-12-27 10:30:04 [INFO] Email sent successfully on attempt 3
```

### Error Classification

**Retryable Errors** (will be retried):
- API timeouts and rate limits
- Network connectivity issues 
- Server errors (5xx)
- Connection refused/DNS failures

**Non-Retryable Errors** (will not be retried):
- Invalid API credentials (401)
- Malformed data (400)
- Invalid email/phone/device tokens
- Resource not found (404)

### Health Response Examples

**Liveness Check Response:**
```json
{
  "status": "alive",
  "service": "notification-service",
  "timestamp": "2024-12-27T10:30:00.123456",
  "uptime_seconds": 3600.5
}
```

**Readiness Check Response:**
```json
{
  "status": "ready",
  "service": "notification-service",
  "timestamp": "2024-12-27T10:30:00.123456",
  "checks": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

**Startup Check Response:**
```json
{
  "status": "started",
  "service": "notification-service",
  "timestamp": "2024-12-27T10:30:00.123456",
  "startup_time": "2024-12-27T10:25:30.123456",
  "initialization_duration_seconds": 270.0
}
```

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

### 🐳 Development Environment (Recommended)

For development, use Docker Compose to start the complete environment with PostgreSQL and Redis:

```bash
# Start all services (PostgreSQL, Redis, and Notification Service)
docker-compose up -d

# View logs
docker-compose logs -f notification-service

# Stop all services
docker-compose down

# Stop and remove volumes (complete reset)
docker-compose down -v
```

**The service will be available at: http://localhost:8003**

#### Production Deployment
```bash
# Production version (without reload)
uvicorn main:app --host 0.0.0.0 --port 8003
```

2. Visit the interactive documentation:
```
http://localhost:8001/docs
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

## 🐳 Docker Compose Details

### Services Included

- **notification-service**: Main application (Port 8003)
- **postgres**: PostgreSQL 15 database (Port 5432)
- **redis**: Redis 7 cache (Port 6379)

### Environment Configuration

The Docker Compose setup includes:

- **Database**: Pre-configured PostgreSQL with health checks
- **Cache**: Redis with persistent storage
- **BulkheadExecutor**: Container-optimized settings
- **Development**: Auto-reload enabled, volume mounting

### Useful Docker Compose Commands

```bash
# Build and start services
docker-compose up --build

# Start only specific services
docker-compose up postgres redis

# Run database migrations (if needed)
docker-compose --profile migration up migrate

# Access development tools container
docker-compose --profile dev-tools up dev-tools
docker-compose exec dev-tools bash

# View service status
docker-compose ps

# View specific service logs
docker-compose logs postgres
docker-compose logs redis

# Restart a specific service
docker-compose restart notification-service

# Scale the notification service
docker-compose up --scale notification-service=3
```

### Health Checks

All services include health checks:
- **PostgreSQL**: `pg_isready` command
- **Redis**: `redis-cli ping` command  
- **Notification Service**: HTTP `/health/live` endpoint

### Data Persistence

Docker volumes are used for data persistence:
- `postgres_data`: Database files
- `redis_data`: Redis persistence

### Troubleshooting

#### Port Conflicts
If you have conflicts with default ports:
```bash
# Edit docker-compose.yml and change port mappings
ports:
  - "5433:5432"  # PostgreSQL on different port
  - "6380:6379"  # Redis on different port
  - "8004:8000"  # Notification service on different port
```

#### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose exec postgres pg_isready -U notification_user

# Connect to database directly
docker-compose exec postgres psql -U notification_user -d notification_service
```

#### Service Not Starting
```bash
# Check service logs
docker-compose logs notification-service

# Check health status
curl http://localhost:8003/health
```

#### Reset Everything
```bash
# Complete reset (removes all data)
docker-compose down -v
docker-compose up -d
```
