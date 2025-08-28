# Notification Service Architecture

## Overview

The Bambu Notification Service is a microservice built using **FastAPI** for handling multi-channel notifications (email, SMS, push) with comprehensive template management, user preferences, and audit logging capabilities.

## Table of Contents

1. [Architectural Decisions](#architectural-decisions)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Data Architecture](#data-architecture)
5. [API Design](#api-design)
6. [GraphQL API](#graphql-api)
7. [Service Layer Architecture](#service-layer-architecture)
8. [Messaging and Adapters](#messaging-and-adapters)
9. [Testing Strategy](#testing-strategy)
10. [Deployment Architecture](#deployment-architecture)
11. [Monitoring and Observability](#monitoring-and-observability)

## Architectural Decisions

### 1. **Clean Architecture Pattern**

**Decision**: Implement layered architecture with clear separation of concerns
- **API Layer**: FastAPI routers and middleware
- **Service Layer**: Business logic and orchestration
- **Repository Layer**: Data access abstraction
- **Model Layer**: Domain entities and data structures

**Rationale**: 
- Promotes maintainability and testability
- Enables independent evolution of each layer
- Facilitates dependency injection and mocking
- Clear boundaries for business logic

### 2. **Async/Await Programming Model**

**Decision**: Use Python's async/await throughout the application
- AsyncSession for database operations
- Async FastAPI endpoints
- Async service methods and repository operations

**Rationale**:
- Better performance under high concurrency
- Non-blocking I/O operations
- Efficient resource utilization
- Natural fit with FastAPI's async capabilities

### 3. **Database-First Approach with SQLAlchemy**

**Decision**: Use SQLAlchemy ORM with PostgreSQL and async drivers
- AsyncPG for database connectivity
- Alembic for migrations
- JSONB for flexible metadata storage

**Rationale**:
- Strong typing and relationship management
- Mature ecosystem and community support
- Excellent async support
- JSONB provides flexibility for notification metadata

### 4. **Multi-Channel Adapter Pattern**

**Decision**: Implement pluggable adapter pattern for notification channels
- Separate adapter classes for Email, SMS, Push
- Common interface for all notification providers
- Dynamic provider loading

**Rationale**:
- Easy to add new notification channels
- Provider-agnostic business logic
- Testable in isolation
- Flexible configuration per channel

### 5. **Template-Driven Notifications**

**Decision**: Template-based notification system with variable substitution
- Stored templates with Jinja2-style variables
- Context-based rendering
- Template versioning support

**Rationale**:
- Separation of content from logic
- Easy content management
- Consistency across channels
- Designer-friendly workflow

### 6. **User Preference Management**

**Decision**: Comprehensive user preference system
- Per-channel enable/disable controls
- Quiet hours support
- Granular notification settings

**Rationale**:
- Regulatory compliance (CAN-SPAM, GDPR)
- Better user experience
- Reduced notification fatigue
- Privacy-first design

### 7. **Comprehensive Audit Logging**

**Decision**: Log all notification attempts with detailed metadata
- Success/failure tracking
- Error message storage
- Response data preservation
- User activity correlation

**Rationale**:
- Debugging and troubleshooting
- Compliance and audit trails
- Analytics and reporting
- Performance monitoring

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│                   API Gateway                       │
│                (Load Balancer)                      │
└─────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────┐
│              Notification Service                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   API v1    │  │ Middleware  │  │   Health    │  │
│  │   Routes    │  │ (Rate Limit │  │   Checks    │  │
│  │             │  │  & CORS)    │  │             │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Service    │  │ Repository  │  │   Models    │  │
│  │   Layer     │  │    Layer    │  │             │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   Email     │  │     SMS     │  │    Push     │  │
│  │  Adapter    │  │   Adapter   │  │   Adapter   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────┐
         │                    │                │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ PostgreSQL  │    │    Redis    │    │  External   │
│  Database   │    │   Cache     │    │ Providers   │
│             │    │             │    │ (SendGrid,  │
│             │    │             │    │  Twilio,    │
│             │    │             │    │   etc.)     │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Technology Stack

### **Core Framework**
- **FastAPI** (0.115.0+): Modern, high-performance web framework
- **Uvicorn**: ASGI server with excellent performance
- **Pydantic** (2.10.0+): Data validation and settings management

### **Database & Storage**
- **PostgreSQL**: Primary database with JSONB support
- **SQLAlchemy** (2.0.25+): Async ORM with modern features
- **AsyncPG** (0.30.0+): High-performance PostgreSQL adapter
- **Alembic** (1.13.0+): Database migration management
- **Redis** (5.2.0+): Caching and rate limiting

### **HTTP & Communication**
- **HTTPX** (0.27.0+): Async HTTP client for external APIs
- **Python-dotenv** (1.0.0+): Environment variable management

### **Development & Testing**
- **Pytest**: Testing framework with async support
- **Coverage**: Code coverage analysis
- **Mock configuration**: Comprehensive mocking infrastructure

## Data Architecture

### **Database Schema**

#### **notification_templates**
```sql
CREATE TABLE notification_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    subject VARCHAR(255),
    body TEXT NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('email', 'sms', 'push')),
    variables JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### **notification_logs**
```sql
CREATE TABLE notification_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    template_id INTEGER REFERENCES notification_templates(id),
    type VARCHAR(20) NOT NULL CHECK (type IN ('email', 'sms', 'push')),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'sent', 'failed', 'bounced')),
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    notification_metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### **user_preferences**
```sql
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    email_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT TRUE,
    push_enabled BOOLEAN DEFAULT TRUE,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### **Indexing Strategy**
- `ix_notification_logs_user_id`: User-based log queries
- `ix_notification_logs_status`: Status filtering
- `ix_notification_logs_type`: Type-based filtering
- `ix_notification_logs_created_at`: Time-based queries
- `ix_notification_templates_type`: Template filtering

### **Data Relationships**
- **Templates → Logs**: One-to-Many relationship
- **User Preferences**: One-per-user with unique constraint
- **JSONB Fields**: Flexible storage for notification metadata and template variables

## API Design

### **RESTful API Principles**
- Resource-based URLs (`/api/v1/templates`, `/api/v1/notifications`)
- HTTP methods aligned with operations (GET, POST, PUT, DELETE)
- Consistent response formats
- Comprehensive error handling

### **Versioning Strategy**
- URL path versioning (`/api/v1/`)
- Backward compatibility maintenance
- Clear deprecation policies

### **Request/Response Patterns**

#### **Pagination**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "size": 50,
  "pages": 3
}
```

#### **Error Responses**
```json
{
  "detail": "Template not found",
  "status_code": 404
}
```

### **Middleware Stack**
1. **CORS Middleware**: Cross-origin resource sharing
2. **Rate Limiting Middleware**: Custom rate limiting with headers
   - Per-minute and per-hour limits
   - Endpoint-specific configurations
   - IP-based tracking
   - Sliding window algorithm

## GraphQL API

### **8. Dual API Strategy (GraphQL + REST)**

**Decision**: Implement both GraphQL and REST APIs to serve different client needs
- **GraphQL**: Flexible query language for complex data fetching
- **REST**: Traditional HTTP API for simple operations
- **Strawberry GraphQL**: Modern Python GraphQL library with async support

**Rationale**:
- **GraphQL Benefits**: Single endpoint, precise data fetching, strong typing
- **REST Benefits**: Caching, simplicity, widespread tooling support
- **Client Flexibility**: Clients can choose the most appropriate API
- **Gradual Migration**: Allows progressive adoption of GraphQL

### **GraphQL Architecture**

#### **Technology Stack**
- **Strawberry GraphQL**: Modern Python GraphQL framework
- **Async Resolvers**: Non-blocking query execution
- **Type Safety**: Strong typing with Python decorators
- **FastAPI Integration**: Seamless integration with existing REST API

#### **Schema Organization**

```python
# graphql/types.py - Type Definitions
@strawberry.type
class NotificationTemplate:
    id: int
    name: str
    subject: Optional[str]
    body: str
    type: NotificationType
    variables: Optional[str]  # JSON string for GraphQL compatibility
    created_at: datetime
    updated_at: datetime

@strawberry.type
class NotificationLog:
    id: int
    user_id: int
    template_id: Optional[int]
    type: NotificationType
    status: NotificationStatus
    sent_at: Optional[datetime]
    error_message: Optional[str]
    metadata: Optional[str]
    created_at: datetime
    template: Optional[NotificationTemplate] = None
```

#### **Query Architecture**

```python
@strawberry.type
class Query:
    """GraphQL Query resolvers"""
    
    @strawberry.field
    async def notification_templates(
        self, 
        pagination: Optional[PaginationInput] = None,
        type_filter: Optional[str] = None
    ) -> NotificationTemplateList:
        """Get all notification templates with filtering and pagination"""
        
    @strawberry.field
    async def notification_template(self, id: int) -> Optional[NotificationTemplate]:
        """Get notification template by ID"""
        
    @strawberry.field
    async def user_notifications(
        self, 
        user_id: int, 
        pagination: Optional[PaginationInput] = None
    ) -> NotificationLogList:
        """Get notifications for a specific user"""
        
    @strawberry.field
    async def user_preferences(self, user_id: int) -> UserPreference:
        """Get user preferences with auto-creation of defaults"""
```

#### **Mutation Architecture**

```python
@strawberry.type
class Mutation:
    """GraphQL Mutation resolvers"""
    
    @strawberry.mutation
    async def send_notification(self, input: NotificationRequestInput) -> NotificationResponse:
        """Send a notification using template and context"""
        
    @strawberry.mutation
    async def create_notification_template(
        self, 
        input: NotificationTemplateCreateInput
    ) -> NotificationTemplate:
        """Create a new notification template"""
        
    @strawberry.mutation
    async def update_notification_template(
        self, 
        id: int, 
        input: NotificationTemplateUpdateInput
    ) -> Optional[NotificationTemplate]:
        """Update existing notification template"""
        
    @strawberry.mutation
    async def update_user_preferences(
        self, 
        user_id: int, 
        input: UserPreferenceUpdateInput
    ) -> UserPreference:
        """Update user notification preferences"""
```

### **GraphQL vs REST Comparison**

| Feature | GraphQL | REST |
|---------|---------|------|
| **Data Fetching** | Precise field selection | Fixed response structure |
| **Network Requests** | Single endpoint | Multiple endpoints |
| **Caching** | Complex (requires normalization) | Simple (HTTP caching) |
| **Tooling** | GraphQL Playground, introspection | Swagger/OpenAPI |
| **Learning Curve** | Steeper | Gentler |
| **Type Safety** | Built-in schema validation | Requires additional tooling |
| **Real-time** | Subscriptions support | WebSocket/SSE required |

### **Input/Output Type System**

#### **Input Types (for Mutations)**
```python
@strawberry.input
class NotificationRequestInput:
    user_id: int
    template_name: str
    context: str  # JSON string for GraphQL compatibility

@strawberry.input
class NotificationTemplateCreateInput:
    name: str
    subject: Optional[str] = None
    body: str
    type: NotificationType
    variables: Optional[str] = None

@strawberry.input
class UserPreferenceUpdateInput:
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
```

#### **Response Types (for Queries)**
```python
@strawberry.type
class NotificationTemplateList:
    items: List[NotificationTemplate]
    pagination: PaginationInfo

@strawberry.type
class PaginationInfo:
    total: int
    page: int
    size: int
    pages: int
```

### **GraphQL Design Patterns**

#### **1. Field-Level Resolution**
- **Lazy Loading**: Template relationships loaded only when requested
- **N+1 Problem Mitigation**: Batch loading for related data
- **Async Resolvers**: Non-blocking field resolution

#### **2. Input Validation**
- **Strawberry Validation**: Built-in input type validation
- **Custom Validators**: Business logic validation in resolvers
- **JSON Handling**: Complex data as JSON strings for GraphQL compatibility

#### **3. Error Handling**
```python
# Comprehensive error handling in resolvers
try:
    # Business logic
    result = await service_operation()
    logger.info(f"✅ GraphQL: Operation successful")
    return result
except Exception as e:
    logger.error(f"💥 GraphQL: Operation failed - error: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise  # GraphQL will handle error formatting
```

### **Integration Strategy**

#### **FastAPI + Strawberry Integration**
```python
# main.py integration
from strawberry.fastapi import GraphQLRouter
from graphql.resolvers import schema

# Add GraphQL endpoint
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")
```

#### **Shared Business Logic**
- **Service Layer Reuse**: Both GraphQL and REST use same service classes
- **Repository Pattern**: Consistent data access across both APIs
- **Validation**: Shared validation logic between REST Pydantic and GraphQL Strawberry

### **GraphQL-Specific Considerations**

#### **Data Type Conversions**
- **JSONB → String**: Complex JSON data serialized as strings for GraphQL
- **Time Objects**: Time fields converted to string representation
- **Enum Mapping**: Python enums mapped to GraphQL enums

#### **Schema Evolution**
- **Additive Changes**: New fields and types without breaking existing queries
- **Deprecation Strategy**: Mark deprecated fields with `@deprecated` directive
- **Versioning**: Schema versioning through field deprecation rather than endpoint versioning

#### **Query Complexity Management**
- **Depth Limiting**: Prevent deeply nested queries
- **Rate Limiting**: Query-based rate limiting (future consideration)
- **Timeout Protection**: Async timeout handling for long-running queries

### **GraphQL Development Tools**

#### **Introspection**
- **Schema Discovery**: Automatic schema documentation
- **Type Information**: Runtime type information for client code generation
- **Field Descriptions**: Comprehensive field documentation

#### **GraphQL Playground**
- **Interactive Explorer**: Query builder and testing interface
- **Schema Documentation**: Auto-generated documentation from schema
- **Query History**: Development and debugging support

### **Example GraphQL Operations**

#### **Query Example**
```graphql
query GetUserNotifications($userId: Int!, $page: Int = 1) {
  userNotifications(userId: $userId, pagination: {page: $page, size: 10}) {
    items {
      id
      type
      status
      sentAt
      createdAt
      template {
        name
        subject
      }
    }
    pagination {
      total
      page
      pages
    }
  }
}
```

#### **Mutation Example**
```graphql
mutation SendNotification($input: NotificationRequestInput!) {
  sendNotification(input: $input) {
    id
    status
    message
    createdAt
  }
}
```

### **Performance Considerations**

#### **Query Optimization**
- **Async Resolvers**: Non-blocking query execution
- **Selective Loading**: Only requested fields are processed
- **Batch Operations**: Efficient handling of list operations

#### **Memory Management**
- **Streaming**: Large result sets handled efficiently
- **Connection Pooling**: Shared database connections
- **Cache Integration**: Redis caching for frequently accessed data

### **Future GraphQL Features**

#### **Real-time Subscriptions**
```python
@strawberry.type
class Subscription:
    @strawberry.subscription
    async def notification_updates(self, user_id: int) -> AsyncGenerator[NotificationLog, None]:
        """Real-time notification updates for a user"""
        # WebSocket-based real-time updates
```

#### **Advanced Features**
- **Federation**: Multi-service GraphQL federation
- **Persisted Queries**: Query caching and optimization
- **Custom Directives**: Advanced query processing
- **DataLoader**: Sophisticated N+1 problem resolution

## Service Layer Architecture

### **Service Organization**

#### **NotificationTemplateService**
- Template CRUD operations
- Template validation and rendering
- Pagination and filtering

#### **NotificationLogService**
- Log creation and retrieval
- User activity tracking
- Audit trail management

#### **UserPreferenceService**
- Preference management
- User consent tracking
- Quiet hours enforcement

#### **NotificationService** (Core)
- Orchestrates notification sending
- Template resolution and rendering
- User preference checking
- Adapter selection and invocation
- **BulkheadExecutor integration** for resilience
- Comprehensive error handling

### **Dependency Injection Pattern**
```python
async def get_notification_service(
    db: AsyncSession = Depends(get_database_session)
) -> NotificationService:
    return NotificationService(db)
```

## Resilience Patterns

### **9. BulkheadExecutor Pattern**

**Decision**: Implement a simplified, container-optimized Bulkhead pattern for resource isolation
- **Separate Thread Pools**: Each notification type (email, SMS, push) gets its own thread pool
- **Timeout Management**: Per-channel timeout configuration
- **Resource Isolation**: Prevents one channel failure from affecting others
- **Container-Friendly**: Minimal resource usage and environment-driven configuration

**Rationale**:
- **Fault Isolation**: Email service downtime doesn't affect SMS delivery
- **Resource Protection**: Prevents resource exhaustion cascade failures
- **Performance Isolation**: Slow email providers don't impact fast SMS delivery
- **Container Efficiency**: Optimized for Docker/Kubernetes deployments
- **Operational Simplicity**: Easy to configure and maintain

### **BulkheadExecutor Architecture**

#### **Core Components**

```python
# Simplified Partition Configuration
@dataclass
class BulkheadConfig:
    max_workers: int = 2          # Thread pool size (container-optimized)
    timeout_seconds: float = 30.0 # Operation timeout
    name: str = "default"         # Partition identifier
```

#### **Default Container-Optimized Configurations**

| Channel | Workers | Timeout | Environment Variable |
|---------|---------|---------|---------------------|
| **Email** | 2-3 | 30s | `BULKHEAD_EMAIL_WORKERS`, `BULKHEAD_EMAIL_TIMEOUT` |
| **SMS** | 1-2 | 15s | `BULKHEAD_SMS_WORKERS`, `BULKHEAD_SMS_TIMEOUT` |
| **Push** | 2-3 | 10s | `BULKHEAD_PUSH_WORKERS`, `BULKHEAD_PUSH_TIMEOUT` |
| **Default** | 2 | 30s | `BULKHEAD_BASE_WORKERS`, `BULKHEAD_BASE_TIMEOUT` |

#### **Partition Isolation**

```python
# Each partition operates independently with simple resource isolation
class BulkheadPartition:
    def __init__(self, config: BulkheadConfig):
        self.config = config
        self.status = PartitionStatus.HEALTHY
        self.total_executions = 0
        self.successful_executions = 0
        self._executor = ThreadPoolExecutor(
            max_workers=config.max_workers,
            thread_name_prefix=f"bulkhead-{config.name}"
        )
```

### **Simplified Health Management**

#### **Health Status Tracking**
- **Execution Metrics**: Simple success/failure counting
- **Status Tracking**: Basic health status per partition
- **Container-Optimized**: Minimal overhead monitoring

#### **Status Enumeration**
```python
class PartitionStatus(Enum):
    HEALTHY = "healthy"  # Normal operation
    FAILED = "failed"    # Recent failures detected
```

### **Usage in NotificationService**

#### **Channel-Specific Execution**
```python
async def send_notification(self, user_id: int, template_name: str, context: Dict[str, Any]):
    # Get bulkhead executor for resilience
    bulkhead_executor = await get_bulkhead_executor()
    
    # Determine partition based on template type
    partition_name = template.type if template.type in ['email', 'sms', 'push'] else 'default'
    
    # Create synchronous wrapper for adapter
    def adapter_send_sync():
        return adapter.send(adapter_context)
    
    # Execute through bulkhead partition
    try:
        result = await bulkhead_executor.execute(partition_name, adapter_send_sync)
        # Handle success...
    except TimeoutError:
        # Handle timeout...
    except RuntimeError as e:
        if "Circuit breaker open" in str(e):
            # Handle circuit breaker...
```

### **Error Handling Strategies**

#### **Timeout Handling**
- **Per-Channel Timeouts**: Different timeout values for each channel
- **Non-blocking Operations**: Async timeout management
- **Graceful Degradation**: Log timeout and continue with other channels

#### **Circuit Breaker Responses**
```python
# Specific error types for different failure modes
return {
    "success": False,
    "error": "Circuit breaker open for partition 'email'",
    "error_type": "circuit_breaker_open",
    "partition": "email"
}
```

### **Health Monitoring**

#### **Partition Health Endpoint**
```python
# GET /health/bulkhead
{
    "status": "healthy",
    "service": "notification-service-bulkhead",
    "partitions": {
        "email": {
            "name": "email",
            "status": "healthy",
            "config": {"max_workers": 10, "timeout_seconds": 30.0},
            "metrics": {
                "total_executions": 1250,
                "successful_executions": 1200,
                "failed_executions": 50,
                "success_rate": 96.0,
                "current_active": 3,
                "consecutive_failures": 0,
                "circuit_open": false
            }
        }
    },
    "summary": {
        "overall_status": "healthy",
        "total_partitions": 4,
        "healthy_partitions": 4,
        "degraded_partitions": 0,
        "failed_partitions": 0
    }
}
```

### **Performance Benefits**

#### **Resource Isolation**
- **Independent Thread Pools**: Each channel has dedicated resources
- **No Cross-Channel Impact**: Email delays don't affect SMS delivery
- **Configurable Resources**: Per-channel worker and timeout tuning

#### **Failure Isolation**
- **Partition-Level Failures**: One channel failure doesn't cascade
- **Automatic Recovery**: Circuit breakers heal automatically
- **Graceful Degradation**: Failed channels don't block successful ones

### **Configuration Management**

#### **Environment-Based Configuration**
```python
# Container-optimized bulkhead configurations via environment variables

def _get_container_configs(self) -> Dict[str, BulkheadConfig]:
    """Get container-optimized configurations"""
    base_workers = int(os.getenv('BULKHEAD_BASE_WORKERS', '2'))
    base_timeout = float(os.getenv('BULKHEAD_BASE_TIMEOUT', '30.0'))
    
    return {
        "email": BulkheadConfig(
            max_workers=int(os.getenv('BULKHEAD_EMAIL_WORKERS', str(base_workers))),
            timeout_seconds=float(os.getenv('BULKHEAD_EMAIL_TIMEOUT', str(base_timeout)))
        ),
        "sms": BulkheadConfig(
            max_workers=int(os.getenv('BULKHEAD_SMS_WORKERS', str(base_workers))),
            timeout_seconds=float(os.getenv('BULKHEAD_SMS_TIMEOUT', '15.0'))
        ),
        "push": BulkheadConfig(
            max_workers=int(os.getenv('BULKHEAD_PUSH_WORKERS', str(base_workers + 1))),
            timeout_seconds=float(os.getenv('BULKHEAD_PUSH_TIMEOUT', '10.0'))
        )
    }
```

#### **Container Deployment Configuration**
```bash
# Environment variables for Docker/Kubernetes deployment
BULKHEAD_BASE_WORKERS=2        # Default worker count
BULKHEAD_EMAIL_WORKERS=3       # Email-specific workers
BULKHEAD_SMS_WORKERS=2         # SMS-specific workers 
BULKHEAD_PUSH_WORKERS=3        # Push-specific workers

# Timeout configurations
BULKHEAD_EMAIL_TIMEOUT=30.0
BULKHEAD_SMS_TIMEOUT=15.0
BULKHEAD_PUSH_TIMEOUT=10.0
```

#### **Production Tuning**
- **Worker Pool Sizing**: Container resource-aware (2-3 workers typical)
- **Timeout Configuration**: Provider-specific SLA requirements
- **Environment-Driven**: All configuration via environment variables

### **Monitoring and Observability**

#### **Key Metrics**
- **Execution Counts**: Total, successful, failed operations per partition
- **Success Rates**: Percentage success rate trending
- **Active Workers**: Current thread utilization
- **Circuit Breaker State**: Open/closed status per partition
- **Timeout Occurrences**: Frequency of timeout events

#### **Alerting Thresholds**
- **Success Rate < 90%**: Warning level alert
- **Circuit Breaker Open**: Critical alert
- **High Timeout Rate**: Performance degradation alert
- **Worker Pool Exhaustion**: Capacity planning alert

### **Testing Strategy**

#### **Unit Tests**
- **Partition Isolation**: Verify independent operation
- **Circuit Breaker Logic**: Failure threshold and recovery testing
- **Timeout Handling**: Async timeout behavior validation
- **Metrics Accuracy**: Counter and status tracking verification

#### **Integration Tests**
- **Multi-Channel Scenarios**: Realistic notification workloads
- **Failure Simulation**: Adapter failures and recovery
- **Performance Testing**: Concurrent load testing
- **Health Endpoint Validation**: Monitoring endpoint accuracy

## Messaging and Adapters

### **Adapter Architecture**

#### **Email Adapter**
- **Provider Interface**: Pluggable email providers
- **Context Mapping**: Email-specific field mapping
- **Error Handling**: Provider-specific error translation

#### **SMS Adapter**
- **Provider Support**: Twilio, AWS SNS, etc.
- **Message Formatting**: Character limits and encoding
- **Delivery Tracking**: Status webhook handling

#### **Push Adapter**
- **Multi-Platform**: iOS (APNs), Android (FCM)
- **Token Management**: Device token validation
- **Payload Optimization**: Platform-specific formatting

### **Provider Selection Strategy**
```python
class NotificationService:
    def __init__(self):
        self.adapters = self._load_adapters()
    
    def _load_adapters(self):
        # Dynamic adapter loading
        # Provider failover support
        # Configuration-based selection
```

## Testing Strategy

### **Test Architecture**

#### **Unit Tests**
- **Mock Configuration**: Comprehensive mocking infrastructure
- **Service Layer**: Business logic validation
- **Repository Layer**: Data access testing
- **Model Layer**: 100% coverage achieved

#### **Integration Tests**
- **API Endpoint Tests**: Full request/response cycles
- **Database Integration**: Real database operations
- **External Service Mocking**: Provider API simulation

#### **Test Coverage Goals**
- **Target**: 80% overall coverage
- **Current**: 44% with strong model coverage (100%)
- **Strategy**: Incremental improvement with priority on critical paths

#### **Mock Infrastructure**
```python
# tests/mock_config.py
class MockDatabase:
    """Comprehensive mock database simulation"""
    
# tests/conftest.py  
"""Centralized fixture management"""
```

### **Test Organization**
- `tests/unit/`: Component-level testing
- `tests/integration/`: End-to-end testing
- `tests/fixtures/`: Shared test data
- `tests/mock_*`: Mock configurations

## Deployment Architecture

### **Containerization**
- **Docker**: Application containerization
- **Multi-stage builds**: Optimized image sizes
- **Health checks**: Built-in readiness/liveness probes

### **Kubernetes Deployment**
```yaml
# Key configurations:
replicas: 3                 # High availability
cpu: 100m-500m             # Resource limits  
memory: 128Mi-512Mi         # Memory constraints
horizontal_pod_autoscaler:  # Auto-scaling
  min: 3, max: 10
  cpu_threshold: 70%
  memory_threshold: 80%
```

### **Health Check Strategy**
- **Startup Probe**: Application initialization
- **Liveness Probe**: Application health monitoring
- **Readiness Probe**: Traffic readiness validation

### **Configuration Management**
- **Environment Variables**: Runtime configuration
- **Kubernetes Secrets**: Sensitive data management
- **ConfigMaps**: Application settings

## Monitoring and Observability

### **Logging Strategy**
- **Structured Logging**: JSON format with correlation IDs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Centralized Collection**: ELK stack or similar
- **Request Tracing**: Full request lifecycle logging

### **Metrics and Monitoring**
- **Rate Limiting Metrics**: Request counts and limits
- **Notification Metrics**: Success/failure rates per channel
- **Performance Metrics**: Response times and throughput
- **Error Tracking**: Exception monitoring and alerting

### **Health Monitoring**
```python
# Multiple health check endpoints:
/health/startup  # Application initialization
/health/live     # Application is running
/health/ready    # Ready to receive traffic
```

### **Rate Limiting Headers**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
X-RateLimit-Window: 60
X-RateLimit-Limit-Minute: 100
X-RateLimit-Remaining-Minute: 95
X-RateLimit-Limit-Hour: 1000
X-RateLimit-Remaining-Hour: 950
```

## Security Considerations

### **Input Validation**
- **Pydantic Models**: Strong typing and validation
- **SQL Injection Prevention**: Parameterized queries
- **XSS Prevention**: Template rendering safety

### **Rate Limiting**
- **IP-based Limiting**: Abuse prevention
- **Endpoint-specific Limits**: Granular control
- **Sliding Window Algorithm**: Accurate rate calculation

### **Data Protection**
- **User Preferences**: Privacy compliance
- **Audit Logging**: Comprehensive activity tracking
- **Sensitive Data Handling**: Minimal retention policies

## Performance Optimizations

### **Database Performance**
- **Strategic Indexing**: Query optimization
- **Connection Pooling**: Efficient resource usage
- **Async Operations**: Non-blocking I/O

### **Caching Strategy**
- **Redis Integration**: Fast data access
- **Template Caching**: Rendered content caching
- **User Preference Caching**: Reduced database load

### **Async Architecture**
- **Non-blocking Operations**: High concurrency support
- **Efficient Resource Usage**: Memory and CPU optimization
- **Scalable Design**: Horizontal scaling support

## Future Architecture Considerations

### **Event-Driven Architecture**
- **Message Queues**: Asynchronous processing
- **Event Sourcing**: Audit trail enhancement
- **CQRS Pattern**: Read/write separation

### **Microservices Evolution**
- **Service Decomposition**: Channel-specific services
- **API Gateway**: Centralized routing and auth
- **Service Mesh**: Inter-service communication

### **Advanced Features**
- **ML-based Optimization**: Send-time optimization
- **Advanced Templates**: Dynamic content personalization
- **Multi-tenant Support**: Organizational isolation

This architecture provides a solid foundation for a scalable, maintainable notification service while maintaining flexibility for future enhancements and requirements.
