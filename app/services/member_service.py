from app.core.exceptions import BadRequestException, NotFoundException, ServiceException
from app.core.logger import logger
from app.core.unit_of_work import AbstractUnitOfWork
from app.enums.role import Role
from app.models.company import Company
from app.models.company_member import CompanyMember
from app.services.permission_service import PermissionService


class MemberService:
    """Service layer for company member management."""

    def __init__(self, uow: AbstractUnitOfWork, permission_service: PermissionService):
        self._uow = uow
        self._permission_service = permission_service

    async def get_company_members(
        self, company_id: int, skip: int, limit: int
    ) -> tuple[list[CompanyMember], int]:
        """
        Get all members of a company (public endpoint).
        """
        async with self._uow:
            try:
                company: Company | None = await self._uow.companies.get_one_by_id(
                    company_id
                )
                if not company:
                    raise NotFoundException(f"Company with id={company_id} not found")

                members, total = await self._uow.company_member.get_members_by_company(
                    company_id, skip, limit
                )
                return members, total

            except NotFoundException:
                raise
            except Exception as e:
                logger.error(
                    f"Error fetching members for company {company_id}: {str(e)}"
                )
                raise ServiceException("Failed to retrieve company members")

    async def remove_member(self, company_id: int, user_id: int, owner_id: int) -> None:
        """
        Owner removes member from company.
        """
        await self._permission_service.require_owner(company_id, owner_id)
        async with self._uow:
            try:
                member = await self._uow.company_member.get_member_by_ids(
                    company_id, user_id
                )
                if not member:
                    raise NotFoundException(
                        f"User {user_id} is not a member of company {company_id}"
                    )

                if member.role == Role.OWNER:
                    raise BadRequestException(
                        "Cannot remove owner from company. Owner must transfer ownership or delete the company."
                    )

                await self._uow.company_member.delete_one(member)
                await self._uow.commit()
                logger.info(
                    f"Member removed: User {user_id} from company {company_id} by owner {owner_id}"
                )

            except (NotFoundException, BadRequestException):
                raise
            except Exception as e:
                logger.error(
                    f"Error removing member {user_id} from company {company_id}: {str(e)}"
                )
                raise ServiceException("Failed to remove member")

    async def leave_company(self, company_id: int, user_id: int) -> None:
        """
        User leaves company.
        """
        async with self._uow:
            try:
                company = await self._uow.companies.get_one_by_id(company_id)
                if not company:
                    raise NotFoundException(f"Company with id={company_id} not found")

                member = await self._uow.company_member.get_member_by_ids(
                    company_id, user_id
                )
                if not member:
                    raise NotFoundException(
                        f"You are not a member of company {company_id}"
                    )

                if member.role == Role.OWNER:
                    raise BadRequestException(
                        "Owner cannot leave the company. You must delete the company or transfer ownership first."
                    )

                await self._uow.company_member.delete_one(member)
                await self._uow.commit()
                logger.info(f"User {user_id} left company {company_id}")

            except (NotFoundException, BadRequestException):
                raise
            except Exception as e:
                logger.error(
                    f"Error user {user_id} leaving company {company_id}: {str(e)}"
                )
                raise ServiceException("Failed to leave company")
