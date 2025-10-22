from fastapi import FastAPI
from app.routers.health import router as health_router
from app.config.cors import setup_cors

app = FastAPI(title="My FastAPI Project")

setup_cors(app)
app.include_router(health_router)
