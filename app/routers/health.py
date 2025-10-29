from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis

router = APIRouter()


@router.get("/")
async def health_check():
    return {"status_code": 200, "detail": "ok", "result": "working"}


@router.get("/health/db")
async def check_database(db: AsyncSession = Depends(get_db)):
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
    try:
        await redis.ping()
        return {"status_code": 200, "detail": "ok", "result": "redis connected"}
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Redis connection failed: {str(e)}"
        )
