# Technical Requirements: Microservice Extraction Challenge

## Core Challenge (3 Hours - Required)

### Objective
Extract the `notifications` service from the provided Django monolith into an independent, deployable microservice.

### Current State
You're provided with a simplified Django project containing three apps:
- `notifications`: Handles email, SMS, and push notifications
- `identity`: User management and authentication
- `payments`: Transaction processing

The notifications app is currently tightly coupled to the other apps through:
- Direct model references
- Shared database
- Synchronous method calls
- Common Django settings

### Requirements

#### 1. Service Architecture (40% of evaluation)

Create a new microservice with this structure:

```
notification-service/
├── api/
│   ├── v1/
│   │   ├── routes.py       # API endpoints
│   │   ├── schemas.py      # Request/response models
│   │   └── middleware.py   # Auth, rate limiting, logging
├── core/
│   ├── models.py           # Domain models
│   ├── services.py         # Business logic
│   └── repositories.py    # Data access layer
├── adapters/
│   ├── email.py           # Email provider integration
│   ├── sms.py             # SMS provider integration
│   └── push.py            # Push notification integration
├── events/
│   ├── publisher.py       # Event publishing
│   └── consumer.py        # Event consumption
├── database/
│   ├── migrations/        # Database migration files
│   └── connection.py      # Database configuration
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

#### 2. API Specification (20% of evaluation)

Design and implement these RESTful endpoints:

**Notification Management**
- `POST /api/v1/notifications/send` - Send a notification
- `GET /api/v1/notifications/{id}` - Get notification details
- `GET /api/v1/notifications/user/{user_id}` - List user notifications
- `PUT /api/v1/notifications/{id}/status` - Update notification status

**Template Management**
- `GET /api/v1/templates` - List all templates
- `POST /api/v1/templates` - Create new template
- `GET /api/v1/templates/{id}` - Get template details
- `PUT /api/v1/templates/{id}` - Update template
- `DELETE /api/v1/templates/{id}` - Delete template

**User Preferences**
- `GET /api/v1/preferences/user/{user_id}` - Get user preferences
- `PUT /api/v1/preferences/user/{user_id}` - Update preferences

**Requirements:**
- OpenAPI/Swagger documentation
- Proper HTTP status codes
- Request validation
- Response pagination for lists
- Rate limiting headers
- API versioning strategy

#### 3. Data Migration (20% of evaluation)

Create a migration strategy for these tables:

```sql
-- Current monolith tables
CREATE TABLE notifications_notificationtemplate (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    subject VARCHAR(255),
    body TEXT NOT NULL,
    type VARCHAR(20) CHECK (type IN ('email', 'sms', 'push')),
    variables JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE notifications_notificationlog (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    template_id INTEGER REFERENCES notifications_notificationtemplate(id),
    type VARCHAR(20) CHECK (type IN ('email', 'sms', 'push')),
    status VARCHAR(20) CHECK (status IN ('pending', 'sent', 'failed', 'bounced')),
    sent_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB
);

CREATE TABLE notifications_userpreference (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    email_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT TRUE,
    push_enabled BOOLEAN DEFAULT TRUE,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Deliverables:**
- Step-by-step migration plan
- Zero-downtime strategy
- Data consistency approach
- Rollback procedures
- Performance considerations

#### 4. Integration Patterns (20% of evaluation)

Implement at least TWO of these patterns:

**A. Circuit Breaker Pattern**
```python
class CircuitBreaker:
    """
    Prevents cascading failures when external services are down
    """
    def __init__(self, failure_threshold=5, timeout=60, half_open_attempts=3):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_attempts = half_open_attempts
        # Implementation required
```

**B. Retry with Exponential Backoff**
```python
@retry(max_attempts=3, backoff_factor=2, max_delay=30)
def send_notification(provider, recipient, message):
    """
    Retry failed notifications with exponential backoff
    """
    # Implementation required
```

**C. Event-Driven Communication**
```json
{
    "event_type": "notification.sent",
    "event_id": "550e8400-e29b-41d4-a716-446655440000",
    "aggregate_id": "notification_123",
    "user_id": 12345,
    "notification_type": "email",
    "template_id": "welcome_email",
    "timestamp": "2024-01-01T00:00:00Z",
    "metadata": {
        "provider": "sendgrid",
        "message_id": "sg_123456"
    }
}
```

**D. Bulkhead Pattern**
```python
class BulkheadExecutor:
    """
    Isolate resources to prevent total system failure
    """
    def __init__(self, max_concurrent_calls=10):
        self.semaphore = threading.Semaphore(max_concurrent_calls)
        # Implementation required
```

## Extension Challenges (3 Hours - Optional)

### Extension 1: Performance Optimization (1 hour)

Given this inefficient code from the monolith:

```python
def get_user_notification_history(user_id, start_date, end_date):
    notifications = []
    
    # Problem 1: Loading all templates
    templates = NotificationTemplate.objects.all()
    
    for template in templates:
        # Problem 2: N+1 query
        logs = NotificationLog.objects.filter(
            user_id=user_id,
            template_id=template.id,
            sent_at__gte=start_date,
            sent_at__lte=end_date
        )
        
        for log in logs:
            # Problem 3: Another N+1 query
            user = User.objects.get(id=user_id)
            
            # Problem 4: No caching
            preference = UserPreference.objects.get(user_id=user_id)
            
            notifications.append({
                'template_name': template.name,
                'user_email': user.email,
                'sent_at': log.sent_at,
                'status': log.status,
                'preferences': {
                    'email': preference.email_enabled,
                    'sms': preference.sms_enabled
                }
            })
    
    # Problem 5: No pagination
    return notifications
```

**Tasks:**
1. Identify all performance issues
2. Provide optimized solution
3. Add appropriate database indexes
4. Implement caching strategy
5. Include benchmark comparisons

### Extension 2: Resilience & Observability (1 hour)

Implement comprehensive resilience patterns:

**A. Health Checks**
```python
GET /health/live     # Is the service running?
GET /health/ready    # Is the service ready to accept requests?
GET /health/startup  # Has the service completed initialization?
```

**B. Graceful Shutdown**
- Complete in-flight requests
- Stop accepting new requests
- Flush logs and metrics
- Close database connections
- Notify load balancer

**C. Metrics & Monitoring**
```python
# Required metrics
notification_sent_total{type="email", status="success"}
notification_sent_duration_seconds{type="sms", quantile="0.99"}
notification_queue_size{queue="high_priority"}
notification_error_rate{type="push", error="provider_timeout"}
```

**D. Distributed Tracing**
- Implement OpenTelemetry
- Trace ID propagation
- Span creation for key operations

### Extension 3: Advanced Event Streaming (1 hour)

Design and implement event streaming architecture:

**A. Event Schema**
```python
@dataclass
class NotificationEvent:
    event_id: UUID
    event_type: str  # notification.requested, notification.sent, notification.failed
    aggregate_id: str
    user_id: int
    correlation_id: str
    causation_id: str
    payload: dict
    metadata: dict
    timestamp: datetime
    version: int
```

**B. Kafka/RabbitMQ Integration**
- Producer with partitioning strategy
- Consumer with exactly-once semantics
- Dead letter queue handling
- Message ordering guarantees

**C. Event Sourcing (Bonus)**
- Event store implementation
- Projection handlers
- Snapshot strategy
- Event replay capability

## Evaluation Criteria

### Code Quality (30%)
- Clean, readable code
- SOLID principles
- Proper error handling
- Type hints
- No code smells

### Architecture (25%)
- Clear separation of concerns
- Dependency injection
- Testability
- Scalability
- Maintainability

### Testing (20%)
- Unit test coverage >80%
- Integration tests for APIs
- Mock external dependencies
- Test fixtures
- Performance tests (bonus)

### Documentation (15%)
- Clear README
- API documentation
- Architecture decisions (ADRs)
- Migration runbook
- Code comments where needed

### DevOps Readiness (10%)
- Dockerfile best practices
- Environment configuration
- CI/CD readiness
- Logging setup
- Monitoring readiness

## Submission Requirements

Your submission should include:

1. **Source Code**
   - Complete microservice implementation
   - All required endpoints
   - At least 2 integration patterns

2. **Documentation**
   - README with setup instructions
   - ARCHITECTURE.md explaining decisions
   - MIGRATION.md with detailed plan
   - API documentation (OpenAPI)

3. **Tests**
   - Unit tests
   - Integration tests
   - Test coverage report

4. **Infrastructure**
   - Dockerfile
   - docker-compose.yml
   - Environment configuration

5. **Diagrams**
   - Current vs proposed architecture
   - Sequence diagrams for key flows
   - Database schema changes

## Success Criteria

A successful submission will:
- Run locally without errors
- Pass all tests
- Have >80% test coverage
- Include comprehensive documentation
- Demonstrate production readiness
- Show clear architectural thinking
- Include at least one extension (for senior roles)