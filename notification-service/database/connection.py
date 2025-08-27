import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import redis.asyncio as redis

# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://notification_user:notification_pass@localhost:5433/notification_service"
)

# Redis setup
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380/0")

# SQLAlchemy setup
engine = None
AsyncSessionLocal = None
Base = declarative_base()

def get_engine():
    """Get or create async database engine"""
    global engine, AsyncSessionLocal
    if engine is None:
        engine = create_async_engine(DATABASE_URL, echo=False)
        AsyncSessionLocal = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
    return engine

# Redis connection
redis_client = None

async def get_redis_client():
    """Get Redis client"""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client

async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    get_engine()  # Ensure engine is initialized
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def close_redis_client():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None

async def close_database():
    """Close database connection"""
    global engine
    if engine:
        await engine.dispose()
