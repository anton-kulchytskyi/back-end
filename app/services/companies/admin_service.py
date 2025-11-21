from app.core.exceptions import BadRequestException, NotFoundException, ServiceException
from app.core.logger import logger
from app.core.unit_of_work import AbstractUnitOfWork
from app.enums.role import Role
from app.models.company_member import CompanyMember
from app.services.companies.company_service import CompanyService
from app.services.companies.permission_service import PermissionService


class AdminService:
    """Service for managing admin roles inside companies."""

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        permission_service: PermissionService,
        company_service: CompanyService,
    ):
        self._uow = uow
        self._permission_service = permission_service
        self._company_service = company_service

    async def _verify_owner_access(self, company_id: int, user_id: int) -> None:
        """Verify company exists and user is owner."""
        await self._company_service.get_company_by_id(company_id)
        await self._permission_service.require_owner(company_id, user_id)

    async def _verify_member_access(self, company_id: int, user_id: int) -> None:
        """Verify company exists and user is member."""
        await self._company_service.get_company_by_id(company_id)
        await self._permission_service.require_member(company_id, user_id)

    async def _get_member_or_raise(
        self, company_id: int, user_id: int
    ) -> CompanyMember:
        """Get member by company_id and user_id or raise NotFoundException."""
        member = await self._uow.company_member.get_member_by_ids(
            company_id=company_id,
            user_id=user_id,
        )
        if not member:
            raise NotFoundException("User is not a member of this company")
        return member

    async def _update_member_role(
        self,
        company_id: int,
        target_user_id: int,
        new_role: Role,
        action: str,
    ) -> CompanyMember:
        """Update member role with proper error handling."""
        async with self._uow:
            try:
                member = await self._get_member_or_raise(company_id, target_user_id)

                member.role = new_role
                await self._uow.commit()

                logger.info(
                    f"User {target_user_id} {action} in company {company_id}: {new_role.value}"
                )

                return member
            except (NotFoundException, BadRequestException):
                raise
            except Exception as e:
                logger.error(
                    f"Error {action} user {target_user_id} in company {company_id}: {str(e)}"
                )
                raise ServiceException(f"Failed to {action} admin")

    async def appoint_admin(
        self,
        company_id: int,
        target_user_id: int,
        current_user_id: int,
    ) -> CompanyMember:
        """
        Promote a member to admin.
        Only owner can do this.
        """
        await self._verify_owner_access(company_id, current_user_id)

        # Check if already admin (early return)
        async with self._uow:
            member = await self._get_member_or_raise(company_id, target_user_id)
            if member.role == Role.ADMIN:
                return member

        return await self._update_member_role(
            company_id=company_id,
            target_user_id=target_user_id,
            new_role=Role.ADMIN,
            action="promoted to admin",
        )

    async def remove_admin(
        self,
        company_id: int,
        target_user_id: int,
        current_user_id: int,
    ) -> CompanyMember:
        """
        Demote admin to member.
        Only owner can do this.
        """
        await self._verify_owner_access(company_id, current_user_id)

        # Validate that user is actually an admin
        async with self._uow:
            member = await self._get_member_or_raise(company_id, target_user_id)
            if member.role != Role.ADMIN:
                raise BadRequestException("User is not an admin")

        return await self._update_member_role(
            company_id=company_id,
            target_user_id=target_user_id,
            new_role=Role.MEMBER,
            action="demoted from admin",
        )

    async def get_admins(
        self,
        current_user_id: int,
        company_id: int,
        skip: int,
        limit: int,
    ) -> tuple[list[CompanyMember], int]:
        """
        Get all administrators for a company.
        Any company member can view admins.
        """
        await self._verify_member_access(company_id, current_user_id)

        async with self._uow:
            try:
                admins, total = await self._uow.company_member.get_admins_by_company(
                    company_id, skip, limit
                )
                return admins, total

            except Exception as e:
                logger.error(
                    f"Error fetching admins for company {company_id}: {str(e)}"
                )
                raise ServiceException("Failed to retrieve company admins")
