from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedException
from app.core.logger import logger
from app.db.company_member_repository import company_member_repository
from app.enums.role import Role


class PermissionService:
    """Service for checking user permissions in companies."""

    async def get_role(
        self, db: AsyncSession, company_id: int, user_id: int
    ) -> str | None:
        """
        Get user's role in the company.
        """
        role = await company_member_repository.get_user_role(db, company_id, user_id)
        return role

    async def require_owner(
        self, db: AsyncSession, company_id: int, user_id: int
    ) -> None:
        """
        Require user to be owner of the company.
        """
        role = await self.get_role(db, company_id, user_id)
        if role != Role.OWNER:
            logger.warning(
                f"Permission denied: User {user_id} (role={role}) tried to perform owner action on company {company_id}"
            )
            raise PermissionDeniedException(
                detail="Only the company owner can perform this action"
            )

    async def require_admin(
        self, db: AsyncSession, company_id: int, user_id: int
    ) -> None:
        """
        Require user to be admin or owner of the company.

        For BE #10 when admin role is added.
        """
        role = await self.get_role(db, company_id, user_id)
        if role not in (Role.ADMIN, Role.OWNER):
            logger.warning(
                f"Permission denied: User {user_id} (role={role}) tried to perform admin action on company {company_id}"
            )
            raise PermissionDeniedException(
                detail="Only company admin or owner can perform this action"
            )

    async def require_member(
        self, db: AsyncSession, company_id: int, user_id: int
    ) -> None:
        """
        Require user to be a member of the company (any role).

        For BE #9+ when member access is needed.
        """
        role = await self.get_role(db, company_id, user_id)
        if role is None:
            logger.warning(
                f"Permission denied: User {user_id} is not a member of company {company_id}"
            )
            raise PermissionDeniedException(
                detail="You must be a company member to perform this action"
            )


# Create instance
permission_service = PermissionService()
