from fastapi import APIRouter

from app.routers.auth import router as auth_router
from app.routers.companies import router as companies_router
from app.routers.health import router as health_router
from app.routers.users import router as users_router

router = APIRouter()

# Register routers here
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(companies_router, prefix="/companies", tags=["Companies"])
router.include_router(health_router, prefix="", tags=["Health"])
router.include_router(users_router, prefix="/users", tags=["Users"])
