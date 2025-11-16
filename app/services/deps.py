from app.services.auth_service import AuthService, auth_service
from app.services.company_service import CompanyService, company_service
from app.services.permission_service import PermissionService, permission_service
from app.services.user_service import UserService, user_service


def get_user_service() -> UserService:
    return user_service


def get_auth_service() -> AuthService:
    return auth_service


def get_company_service() -> CompanyService:
    return company_service


def get_permission_service() -> PermissionService:
    return permission_service
