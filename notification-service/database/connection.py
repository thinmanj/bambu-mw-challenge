import os
import redis.asyncio as redis

# Database setup (simplified for now)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://notification_user:notification_pass@localhost:5433/notification_service"
)

# Redis setup
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380/0")

# Redis connection
redis_client = None

# Database session will be implemented later when needed

async def get_redis_client():
    """Get Redis client"""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client

async def close_redis_client():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
