from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.redis import get_redis
from app.core.unit_of_work import AbstractUnitOfWork, SQLAlchemyUnitOfWork
from app.models import User
from app.services import (
    AdminService,
    AuthService,
    CompanyService,
    InvitationService,
    MemberService,
    PermissionService,
    QuizAttemptService,
    QuizService,
    RedisQuizService,
    RequestService,
    UserService,
)
from app.services.analytics.company_analytics_service import CompanyAnalyticsService
from app.services.analytics.user_analytics_service import UserAnalyticsService
from app.services.notification.notification_service import NotificationService
from app.services.quiz.quiz_export_service import QuizExportService


def get_uow() -> AbstractUnitOfWork:
    return SQLAlchemyUnitOfWork()


def get_notification_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> NotificationService:
    return NotificationService(uow=uow)


def get_redis_quiz_service() -> RedisQuizService:
    redis = get_redis()
    return RedisQuizService(redis)


def get_user_service(uow: AbstractUnitOfWork = Depends(get_uow)) -> UserService:
    return UserService(uow=uow)


def get_auth_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
    user_service: UserService = Depends(get_user_service),
) -> AuthService:
    return AuthService(uow=uow, user_service=user_service)


def get_permission_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> PermissionService:
    return PermissionService(uow=uow)


def get_company_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
    permission_service: PermissionService = Depends(get_permission_service),
) -> CompanyService:
    return CompanyService(uow=uow, permission_service=permission_service)


def get_member_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
    permission_service: PermissionService = Depends(get_permission_service),
) -> MemberService:
    return MemberService(uow=uow, permission_service=permission_service)


def get_admin_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
    permission_service: PermissionService = Depends(get_permission_service),
    company_service: CompanyService = Depends(get_company_service),
) -> AdminService:
    return AdminService(
        uow=uow, permission_service=permission_service, company_service=company_service
    )


def get_invitation_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
    permission_service: PermissionService = Depends(get_permission_service),
) -> InvitationService:
    return InvitationService(uow=uow, permission_service=permission_service)


def get_request_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
    permission_service: PermissionService = Depends(get_permission_service),
) -> RequestService:
    return RequestService(uow=uow, permission_service=permission_service)


def get_quiz_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
    permission_service: PermissionService = Depends(get_permission_service),
    notification_service: NotificationService = Depends(get_notification_service),
) -> QuizService:
    return QuizService(
        uow=uow,
        permission_service=permission_service,
        notification_service=notification_service,
    )


def get_quiz_attempt_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
    permission_service: PermissionService = Depends(get_permission_service),
    quiz_service: QuizService = Depends(get_quiz_service),
    redis_quiz_service: RedisQuizService = Depends(get_redis_quiz_service),
) -> QuizAttemptService:
    return QuizAttemptService(
        uow=uow,
        permission_service=permission_service,
        quiz_service=quiz_service,
        redis_quiz_service=redis_quiz_service,
    )


def get_quiz_export_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
    permission_service: PermissionService = Depends(get_permission_service),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> QuizExportService:
    return QuizExportService(
        uow=uow,
        permission_service=permission_service,
        quiz_service=quiz_service,
    )


def get_user_analytics_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
) -> UserAnalyticsService:
    return UserAnalyticsService(uow=uow)


def get_company_analytics_service(
    uow: AbstractUnitOfWork = Depends(get_uow),
    admin_service: AdminService = Depends(get_admin_service),
) -> CompanyAnalyticsService:
    return CompanyAnalyticsService(
        uow=uow,
        admin_service=admin_service,
    )


# HTTPBearer scheme for token authentication
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Dependency to get current authenticated user from token.

    Supports both authentication methods:
    - JWT token (HS256) from POST /auth/login
    - Auth0 token (RS256) from Auth0 flow
    """
    token = credentials.credentials
    return await auth_service.get_current_user_from_token(token)
