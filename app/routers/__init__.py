from fastapi import APIRouter

from app.routers.health import router as health_router

router = APIRouter()

# Register routers here
router.include_router(health_router, prefix="", tags=["Health"])
