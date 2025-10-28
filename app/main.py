from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.core.database import close_db, init_db
from app.core.redis import close_redis, init_redis
from app.routers import router


# Lifespan context manager for startup and shutdown events.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting application...!")
    await init_db()
    print("✅ PostgreSQL connected successfully")
    await init_redis()

    yield

    # Shutdown
    print("🛑 Shutting down application...")
    await close_db()
    print("✅ PostgreSQL connection closed")
    await close_redis()


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
    )
