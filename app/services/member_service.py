from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    PermissionDeniedException,
    ServiceException,
)
from app.core.logger import logger
from app.db.company_member_repository import company_member_repository
from app.db.company_repository import company_repository
from app.enums.role import Role
from app.models.company_member import CompanyMember
from app.services.permission_service import permission_service


class MemberService:
    """Service layer for company member management."""

    async def get_company_members(
        self, db: AsyncSession, company_id: int, skip: int, limit: int
    ) -> tuple[list[CompanyMember], int]:
        """
        Get all members of a company (public endpoint).
        """
        try:
            company = await company_repository.get_one(db, company_id)
            if not company:
                raise NotFoundException(f"Company with id={company_id} not found")

            from sqlalchemy import func, select

            count_stmt = (
                select(func.count())
                .select_from(CompanyMember)
                .where(CompanyMember.company_id == company_id)
            )
            result = await db.execute(count_stmt)
            total = result.scalar_one()

            stmt = (
                select(CompanyMember)
                .where(CompanyMember.company_id == company_id)
                .order_by(
                    CompanyMember.role.desc(),
                    CompanyMember.created_at.asc(),
                )
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(stmt)
            members = list(result.scalars().all())

            return members, total

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error fetching members for company {company_id}: {str(e)}")
            raise ServiceException("Failed to retrieve company members")

    async def remove_member(
        self, db: AsyncSession, company_id: int, user_id: int, owner_id: int
    ) -> None:
        """
        Owner removes member from company.
        """
        try:
            await permission_service.require_owner(db, company_id, owner_id)

            member = await company_member_repository.get_member(db, company_id, user_id)
            if not member:
                raise NotFoundException(
                    f"User {user_id} is not a member of company {company_id}"
                )

            if member.role == Role.OWNER:
                raise BadRequestException(
                    "Cannot remove owner from company. Owner must transfer ownership or delete the company."
                )

            await company_member_repository.delete_one(db, member)
            logger.info(
                f"Member removed: User {user_id} from company {company_id} by owner {owner_id}"
            )

        except (PermissionDeniedException, NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(
                f"Error removing member {user_id} from company {company_id}: {str(e)}"
            )
            raise ServiceException("Failed to remove member")

    async def leave_company(
        self, db: AsyncSession, company_id: int, user_id: int
    ) -> None:
        """
        User leaves company.
        """
        try:
            company = await company_repository.get_one(db, company_id)
            if not company:
                raise NotFoundException(f"Company with id={company_id} not found")

            member = await company_member_repository.get_member(db, company_id, user_id)
            if not member:
                raise NotFoundException(f"You are not a member of company {company_id}")

            if member.role == Role.OWNER:
                raise BadRequestException(
                    "Owner cannot leave the company. You must delete the company or transfer ownership first."
                )

            await company_member_repository.delete_one(db, member)
            logger.info(f"User {user_id} left company {company_id}")

        except (NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(f"Error user {user_id} leaving company {company_id}: {str(e)}")
            raise ServiceException("Failed to leave company")


# Create instance
member_service = MemberService()
