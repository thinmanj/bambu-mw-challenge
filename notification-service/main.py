import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from api.v1 import api_v1_router
from database.connection import get_redis_client, close_redis_client

# Initialize FastAPI app
app = FastAPI(
    title="Bambu Notification Service",
    description="Microservice for handling notifications (email, SMS, push)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include versioned API routers
app.include_router(api_v1_router)

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    # Initialize Redis connection
    await get_redis_client()

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    await close_redis_client()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "notification-service",
        "version": "1.0.0",
        "status": "running",
        "api_versions": ["v1"],
        "api_base_url": "/api/v1"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration"""
    # TODO: Add database and redis connectivity checks
    return {
        "status": "healthy",
        "service": "notification-service",
        "database": "connected",  # Will be implemented
        "cache": "connected"      # Will be implemented
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)
