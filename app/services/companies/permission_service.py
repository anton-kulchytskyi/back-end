from app.core.exceptions import PermissionDeniedException
from app.core.logger import logger
from app.core.unit_of_work import AbstractUnitOfWork
from app.enums.role import Role


class PermissionService:
    """Service for checking user permissions in companies."""

    def __init__(self, uow: AbstractUnitOfWork):
        self._uow = uow

    async def get_role(self, company_id: int, user_id: int) -> str | None:
        """
        Get user's role in the company.
        """
        async with self._uow:
            role = await self._uow.company_member.get_member_role(company_id, user_id)
            return role

    async def require_owner(self, company_id: int, user_id: int) -> None:
        """
        Require user to be owner of the company.
        """
        role = await self.get_role(company_id, user_id)
        if role != Role.OWNER:
            logger.warning(
                f"Permission denied: User {user_id} (role={role}) tried to perform owner action on company {company_id}"
            )
            raise PermissionDeniedException(
                detail="Only the company owner can perform this action"
            )

    async def require_admin(self, company_id: int, user_id: int) -> None:
        """
        Require user to be admin or owner of the company.

        For BE #10 when admin role is added.
        """
        role = await self.get_role(company_id, user_id)
        if role not in (Role.ADMIN, Role.OWNER):
            logger.warning(
                f"Permission denied: User {user_id} (role={role}) tried to perform admin action on company {company_id}"
            )
            raise PermissionDeniedException(
                detail="Only company admin or owner can perform this action"
            )

    async def require_member(self, company_id: int, user_id: int) -> None:
        """
        Require user to be a member of the company (any role).

        For BE #9+ when member access is needed.
        """
        role = await self.get_role(company_id, user_id)
        if role is None:
            logger.warning(
                f"Permission denied: User {user_id} is not a member of company {company_id}"
            )
            raise PermissionDeniedException(
                detail="You must be a company member to perform this action"
            )
