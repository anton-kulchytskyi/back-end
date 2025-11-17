from app.services.auth_service import AuthService, auth_service
from app.services.company_service import CompanyService, company_service
from app.services.invitation_service import InvitationService, invitation_service
from app.services.member_service import MemberService, member_service
from app.services.permission_service import PermissionService, permission_service
from app.services.request_service import RequestService, request_service
from app.services.user_service import UserService, user_service


def get_auth_service() -> AuthService:
    return auth_service


def get_company_service() -> CompanyService:
    return company_service


def get_invitation_service() -> InvitationService:
    return invitation_service


def get_member_service() -> MemberService:
    return member_service


def get_permission_service() -> PermissionService:
    return permission_service


def get_request_service() -> RequestService:
    return request_service


def get_user_service() -> UserService:
    return user_service
