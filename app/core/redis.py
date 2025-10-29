from redis.asyncio import Redis

from app.config import settings

# Global Redis client
redis_client: Redis | None = None


def get_redis() -> Redis:
    global redis_client

    if redis_client is None:
        redis_client = Redis.from_url(
            settings.redis.REDIS_URL,
            decode_responses=True,
        )

    return redis_client
