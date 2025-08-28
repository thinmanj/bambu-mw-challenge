#!/bin/bash

# Docker entrypoint script with graceful shutdown handling

set -e

# Set up signal handlers for graceful shutdown
cleanup() {
    echo "Received shutdown signal, performing cleanup..."
    # Kill the main process gracefully
    if [ -n "$MAIN_PID" ]; then
        kill -TERM "$MAIN_PID" 2>/dev/null || true
        wait "$MAIN_PID" 2>/dev/null || true
    fi
    echo "Cleanup completed"
    exit 0
}

# Trap signals for graceful shutdown
trap cleanup SIGTERM SIGINT SIGQUIT

# Log container startup
echo "Starting notification service container..."
echo "Environment: ${ENVIRONMENT:-development}"
echo "Log level: ${LOG_LEVEL:-INFO}"

# Show bulkhead configuration
echo "Bulkhead configuration:"
echo "  Base workers: ${BULKHEAD_BASE_WORKERS:-2}"
echo "  Email workers: ${BULKHEAD_EMAIL_WORKERS:-2}"
echo "  SMS workers: ${BULKHEAD_SMS_WORKERS:-2}"
echo "  Push workers: ${BULKHEAD_PUSH_WORKERS:-3}"

# Check if we need to run migrations (only if DATABASE_URL is set)
if [ -n "$DATABASE_URL" ] && [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head || {
        echo "Migration failed, continuing anyway..."
    }
fi

# Start the application
echo "Starting FastAPI application..."
exec python -m uvicorn main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 1 \
    --loop uvloop \
    --log-level ${LOG_LEVEL:-info} &

MAIN_PID=$!

# Wait for the main process
wait $MAIN_PID
