import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logger import logger
from app.routers import router

app = FastAPI(title=settings.app.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.get_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

logger.info("Starting FastAPI application...")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.app.HOST,
        port=settings.app.PORT,
        reload=settings.app.RELOAD,
    )
