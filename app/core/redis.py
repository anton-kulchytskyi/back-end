from redis.asyncio import Redis, ConnectionPool
from app.config.settings import settings

# Global Redis client
redis_client: Redis | None = None


async def init_redis() -> None:
    global redis_client
    
    pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=10,
        decode_responses=True,
    )
    
    redis_client = Redis(connection_pool=pool)
    
    # Test connection
    await redis_client.ping()
    print("✅ Redis connected successfully")


async def close_redis() -> None:
    global redis_client
    
    if redis_client:
        await redis_client.aclose()
        print("✅ Redis connection closed")

# Dependency for getting Redis client.
async def get_redis() -> Redis:
    if redis_client is None:
        raise RuntimeError("Redis client is not initialized")
    return redis_client