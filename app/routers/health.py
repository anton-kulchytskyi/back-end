from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_raw_session
from app.core.redis import get_redis

router = APIRouter()


def _extract_host(url: str) -> str:
    return urlparse(url).hostname or "unknown"


@router.get("/")
async def health_check():
    """
    Core Application Health Check

    Checks if the basic FastAPI service is running and accessible.
    """
    return {"status_code": 200, "detail": "ok", "result": "working"}


@router.get("/health/db")
async def check_database(db: AsyncSession = Depends(get_raw_session)):
    """
    Database Connection Check

    Executes a simple "SELECT 1" query to verify an active connection
    to the underlying database (e.g., PostgreSQL/SQLAlchemy).

    Raises:
        HTTPException: 503 Service Unavailable, if the database connection fails.
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        return {"status_code": 200, "detail": "ok", "result": "database connected"}
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Database connection failed: {str(e)}"
        )


@router.get("/health/redis")
async def check_redis(redis: Redis = Depends(get_redis)):
    """
    Redis Connection Check

    Executes a PING command to verify an active connection to the Redis cache server.

    Raises:
        HTTPException: 503 Service Unavailable, if the Redis connection fails.
    """
    try:
        await redis.ping()
        return {"status_code": 200, "detail": "ok", "result": "redis connected"}
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Redis connection failed: {str(e)}"
        )


@router.get("/health/all")
async def check_all(
    db: AsyncSession = Depends(get_raw_session),
    redis: Redis = Depends(get_redis),
):
    """
    Full Health Check

    Checks both PostgreSQL and Redis connectivity in a single call.
    Returns the connection status, source environment (local / railway),
    and the resolved host for each service.
    """
    db_host = _extract_host(settings.database.DATABASE_URL)
    redis_host = _extract_host(settings.redis.REDIS_URL)

    is_railway = settings.database.DATABASE_SSL
    db_source = "railway" if is_railway else "local"
    redis_source = "railway" if is_railway else "local"

    db_status, db_error = "ok", None
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
    except Exception as e:
        db_status, db_error = "error", str(e)

    redis_status, redis_error = "ok", None
    try:
        await redis.ping()
    except Exception as e:
        redis_status, redis_error = "error", str(e)

    overall = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"

    return {
        "status": overall,
        "database": {
            "status": db_status,
            "source": db_source,
            "host": db_host,
            **({"error": db_error} if db_error else {}),
        },
        "redis": {
            "status": redis_status,
            "source": redis_source,
            "host": redis_host,
            **({"error": redis_error} if redis_error else {}),
        },
    }
