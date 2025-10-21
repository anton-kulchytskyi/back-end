from fastapi import FastAPI
from app.routers.health import router as health_router

app = FastAPI(title="My FastAPI Project")

app.include_router(health_router)
