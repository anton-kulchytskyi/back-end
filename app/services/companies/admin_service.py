from app.core.exceptions import BadRequestException, NotFoundException, ServiceException
from app.core.logger import logger
from app.core.unit_of_work import AbstractUnitOfWork
from app.models.company import Company
from app.models.company_member import CompanyMember, Role
from app.services.companies.permission_service import PermissionService


class AdminService:
    """Service for managing admin roles inside companies."""

    def __init__(self, uow: AbstractUnitOfWork, permission_service: PermissionService):
        self._uow = uow
        self._permission_service = permission_service

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
        await self._permission_service.require_owner(company_id, current_user_id)

        async with self._uow:
            try:
                member = await self._uow.company_member.get_member_by_ids(
                    company_id=company_id,
                    user_id=target_user_id,
                )

                if not member:
                    raise NotFoundException("User is not a member of this company")

                if member.role == Role.ADMIN:
                    return member

                member.role = Role.ADMIN
                await self._uow.commit()

                logger.info(
                    f"User {target_user_id} promoted to admin in company {company_id}"
                )

                return member
            except NotFoundException:
                raise
            except Exception as e:
                logger.error(
                    f"Error appoint user {target_user_id} to admin for company {company_id}: {str(e)}"
                )
                raise ServiceException("Failed to appoint admin")

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
        await self._permission_service.require_owner(company_id, current_user_id)

        async with self._uow:
            try:
                member = await self._uow.company_member.get_member_by_ids(
                    company_id=company_id,
                    user_id=target_user_id,
                )

                if not member:
                    raise NotFoundException("User is not a member of this company")

                if member.role != Role.ADMIN:
                    raise BadRequestException("User is not an admin")

                member.role = Role.MEMBER
                await self._uow.commit()

                logger.info(
                    f"User {target_user_id} demoted from admin in company {company_id}"
                )

                return member
            except NotFoundException:
                raise
            except Exception as e:
                logger.error(
                    f"Error appoint user {target_user_id} to admin for company {company_id}: {str(e)}"
                )
                raise ServiceException("Failed to appoint admin")

    async def get_admins(
        self, current_user_id, company_id: int, skip: int, limit: int
    ) -> tuple[list[CompanyMember], int]:
        """
        Get all administrators for a company.
        Any company member can view admins.
        """
        await self._permission_service.require_member(company_id, current_user_id)

        async with self._uow:
            try:
                company: Company | None = await self._uow.companies.get_one_by_id(
                    company_id
                )
                if not company:
                    raise NotFoundException(f"Company with id={company_id} not found")

                admins, total = await self._uow.company_member.get_admins_by_company(
                    company_id, skip, limit
                )
                return admins, total

            except Exception as e:
                logger.error(
                    f"Error fetching admins for company {company_id}: {str(e)}"
                )
                raise ServiceException("Failed to retrieve company admins")
