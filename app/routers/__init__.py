from fastapi import APIRouter

from app.routers.analytics.company_analytics import router as company_analytics_router
from app.routers.analytics.user_analytics import router as user_analytics_router
from app.routers.auth import router as auth_router
from app.routers.companies.admins import router as company_admins_router
from app.routers.companies.companies import router as companies_router
from app.routers.companies.company_actions import router as company_actions_router
from app.routers.health import router as health_router
from app.routers.invitations import router as invitations_router
from app.routers.quizzes.qiuzzes import router as quizzes_router
from app.routers.quizzes.quiz_attempts import router as quiz_attempt_router
from app.routers.quizzes.quiz_export import router as export_router
from app.routers.requests import router as requests_router
from app.routers.users import router as users_router

router = APIRouter()


# Register routers here
router.include_router(
    company_analytics_router,
    prefix="/analytics/companies",
    tags=["Analytics Companies"],
)
router.include_router(
    user_analytics_router, prefix="/analytics/me", tags=["Analytics User"]
)
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(
    company_admins_router,
    prefix="/companies/{company_id}/admins",
    tags=["Companies - Admins"],
)
router.include_router(companies_router, prefix="/companies", tags=["Companies"])
router.include_router(
    company_actions_router, prefix="/companies", tags=["Company Actions"]
)
router.include_router(
    quizzes_router, prefix="/companies/{company_id}/quizzes", tags=["Quizzes"]
)
router.include_router(
    quiz_attempt_router, prefix="/quiz-attempts", tags=["Quiz Attempts"]
)
router.include_router(health_router, prefix="", tags=["Health"])
router.include_router(invitations_router, prefix="/invitations", tags=["Invitations"])
router.include_router(export_router, prefix="/export", tags=["Export"])
router.include_router(requests_router, prefix="/requests", tags=["Requests"])
router.include_router(users_router, prefix="/users", tags=["Users"])
