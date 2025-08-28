# Notification Service

A FastAPI-based microservice for sending, templating, and tracking notifications across multiple channels (email, SMS, push). It provides a clean REST API with standardized Pydantic schemas, optional GraphQL demo, resilience patterns (bulkhead executor, retries), and comprehensive test coverage.

- REST API with OpenAPI/Swagger docs
- Standardized schema models (no SQLAlchemy dependencies in API schemas)
- Rate limiting middleware with standard X-RateLimit-* headers
- Simplified, container-optimized BulkheadExecutor for resilience
- Retry decorators with tenacity integration and documentation
- Health endpoints for liveness, readiness, and startup probes
- Detailed logging to stdout and file where configured

For deeper architecture and migration strategy:
- Architecture overview: see ../ARCHITECTURE.md
- Migration plan (monolith → microservice): see ../MIGRATION.md
- API usage details: see API_README.md


## Table of contents
- Overview
- Project layout
- Getting started (development)
  - Using Docker Compose (recommended)
  - Running locally without Docker (optional)
- Configuration
- Running tests and coverage
- API documentation
- Health checks
- Production deployment
  - Container image
  - Database migrations
  - Kubernetes deployment tips
  - Observability
- GraphQL demo (optional)
- Troubleshooting


## Project layout

Key paths:
- notification-service/                    ← This service
  - api/                                   ← FastAPI routers and schemas
  - core/                                  ← Business logic, adapters, resilience
  - tests/                                 ← Unit and integration tests
  - Dockerfile, docker-entrypoint.sh       ← Container build and startup scripts
  - API_README.md                          ← Detailed API docs
- MIGRATION.md                             ← End-to-end migration plan
- ARCHITECTURE.md                          ← System architecture docs
- docker-compose.yml                       ← Root-level dev environment (Postgres, Redis, service)


## Getting started (development)

### Prerequisites
- Docker and Docker Compose
- Python 3.12+ (only if running locally without Docker)


### Using Docker Compose (recommended)
From the repository root (where docker-compose.yml lives):

1) Build and start the services in the background
- docker compose up -d --build

2) Check logs
- docker compose logs -f notification-service

3) Access the API
- REST Swagger UI: http://localhost:8001/docs
- OpenAPI JSON: http://localhost:8001/openapi.json

4) Verify health
- Liveness:  http://localhost:8001/health/liveness
- Readiness: http://localhost:8001/health/readiness
- Startup:   http://localhost:8001/health/startup

Notes:
- The Compose file also provisions Postgres and Redis. Ensure ports are free on your machine.
- If database migrations are enabled (RUN_MIGRATIONS=true), they should execute on container start. See “Database migrations”.


### Running locally without Docker (optional)
Only recommended if you already have Postgres and Redis running locally and are comfortable managing Python dependencies.

1) Set environment variables (examples below in “Configuration”).
2) Create and activate a virtual environment.
3) Install dependencies (pip):
- pip install -r requirements.txt

4) Start the API server
- uvicorn notification_service.main:app --host 0.0.0.0 --port 8001 --log-level info

5) Open http://localhost:8001/docs


## Configuration
Set via environment variables (examples):
- PORT=8001
- LOG_LEVEL=info
- DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/notifications
- REDIS_URL=redis://redis:6379/0
- RUN_MIGRATIONS=true
- CORS_ALLOW_ORIGINS=*
- RATE_LIMIT_GLOBAL=100/minute

Guidance:
- DATABASE_URL must use asyncpg for async SQLAlchemy engines.
- Keep secrets out of shell history; use a secrets manager or Docker/Kubernetes secret objects.
- For rate limiting, you can configure global and per-endpoint limits; the middleware injects X-RateLimit-* headers.


## Running tests and coverage
From the notification-service directory:
- pytest -q
- pytest -q --maxfail=1 -k "unit and not integration"
- pytest --cov=notification_service --cov-report=term-missing

Notes:
- Some integration tests may expect Postgres/Redis. Use Docker Compose for the full stack.
- Mock-based unit tests are provided to avoid circular imports and heavy dependencies.


## API documentation
- High-level API usage and examples: see API_README.md
- Live docs when running the service: http://localhost:8001/docs

All endpoints use standardized Pydantic schema models for request/response, including notification logs, templates, and user preferences. The notification status update endpoint is available at:
- PUT /api/v1/notifications/{id}/status


## Health checks
The service exposes standard health endpoints:
- GET /health/liveness
- GET /health/readiness
- GET /health/startup

The readiness endpoint checks core dependencies (e.g., DB/Redis) and returns HTTP 503 if not ready. Use these endpoints for container health probes in Docker/Kubernetes.


## Production deployment

### Container image
Build and push an image:
- docker build -t your-registry/notification-service:VERSION .
- docker push your-registry/notification-service:VERSION

Recommended runtime environment variables (examples):
- PORT=8002
- LOG_LEVEL=info
- DATABASE_URL=postgresql+asyncpg://user:password@db:5432/notifications
- REDIS_URL=redis://redis:6379/0
- RUN_MIGRATIONS=true

If using the provided docker-entrypoint.sh, RUN_MIGRATIONS=true will attempt to run migrations on startup.


### Database migrations
- Ensure the migrations directory and alembic config are mounted or baked into the image as needed.
- In Compose or Kubernetes, set RUN_MIGRATIONS=true to run at startup, or run a one-off job that executes migrations prior to deploying the app pods.
- Observe logs to verify that migrations applied successfully.


### Kubernetes deployment tips
- Use separate Deployment for the web app and a Job or initContainer for DB migrations.
- Configure readiness, liveness, and startup probes pointing to the /health/* endpoints.
- Set resource requests/limits; the service uses a simplified bulkhead executor designed for container environments.
- Use ConfigMap/Secret for non-sensitive/sensitive configuration.
- Expose the service via ClusterIP/Ingress as needed.

Probe examples (illustrative):
- readinessProbe: GET /health/readiness
- livenessProbe:  GET /health/liveness
- startupProbe:   GET /health/startup


### Observability
- Logs: emitted to stdout; can be collected by your platform (e.g., Fluent Bit, CloudWatch, Stackdriver). A file logger may be enabled depending on configuration.
- Rate limiting: responses include X-RateLimit-* headers.
- Bulkhead executor: basic partition metrics are surfaced via the health endpoints for monitoring.


## Troubleshooting
- Health endpoints return 503:
  - Verify database connectivity and credentials.
  - Ensure migrations have executed successfully (RUN_MIGRATIONS=true or manual run).
  - Check Redis connectivity if enabled in readiness checks.
- Import/circular dependency issues when running tests:
  - Prefer running tests via Docker Compose or use the provided mock-based unit tests.
- Async driver errors:
  - Confirm DATABASE_URL uses asyncpg (postgresql+asyncpg://...).


## References
- Architecture: ../ARCHITECTURE.md
- Migration guide: ../MIGRATION.md
- API details: API_README.md

