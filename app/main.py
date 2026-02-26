from contextlib import asynccontextmanager

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logger import logger
from app.routers import router
from app.services.scheduler.quiz_reminder_service import QuizReminderService


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()
    reminder_service = QuizReminderService()

    scheduler.add_job(
        reminder_service.send_quiz_reminders,
        trigger=CronTrigger(hour=0, minute=0),
        id="quiz_reminders",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started — quiz reminders will run daily at midnight")

    yield

    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")


app = FastAPI(title=settings.app.PROJECT_NAME, lifespan=lifespan)

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
