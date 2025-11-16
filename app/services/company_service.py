from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import PermissionDeniedException, ServiceException
from app.core.logger import logger
from app.db.company_member_repository import company_member_repository
from app.db.company_repository import company_repository
from app.enums.role import Role
from app.models.company import Company
from app.models.company_member import CompanyMember
from app.schemas.company import CompanyCreateRequest, CompanyUpdateRequest
from app.services.permission_service import permission_service


class CompanyService:
    """Service layer for company operations."""

    async def create_company(
        self, db: AsyncSession, company_data: CompanyCreateRequest, owner_id: int
    ) -> Company:
        """
        Create a new company and assign creator as owner.
        """
        try:
            company = Company(
                name=company_data.name,
                description=company_data.description,
                owner_id=owner_id,
                is_visible=True,
            )
            created_company = await company_repository.create_one(db, company)

            member = CompanyMember(
                company_id=created_company.id, user_id=owner_id, role=Role.OWNER
            )
            await company_member_repository.create_one(db, member)

            logger.info(
                f"Company created: {created_company.name} (ID: {created_company.id}) by user {owner_id}"
            )
            return created_company

        except Exception as e:
            logger.error(f"Error creating company: {str(e)}")
            raise ServiceException("Failed to create company")

    async def get_all_companies(
        self, db: AsyncSession, skip: int, limit: int
    ) -> tuple[list[Company], int]:
        """
        Get all companies (paginated).
        """
        try:
            return await company_repository.get_visible_companies(db, skip, limit)

        except Exception as e:
            logger.error(f"Error fetching companies: {str(e)}")
            raise ServiceException("Failed to retrieve companies")

    async def get_company_by_id(self, db: AsyncSession, company_id: int) -> Company:
        """
        Get company by ID.
        """
        try:
            company = await company_repository.get_one(db, company_id)
            if not company:
                raise ServiceException(f"Company with ID {company_id} not found")
            return company

        except ServiceException:
            raise
        except Exception as e:
            logger.error(f"Error fetching company {company_id}: {str(e)}")
            raise ServiceException("Failed to retrieve company")

    async def update_company(
        self,
        db: AsyncSession,
        company: Company,
        company_data: CompanyUpdateRequest,
        current_user_id: int,
    ) -> Company:
        """
        Update company information.
        Only owner can update the company.
        """
        try:
            await permission_service.require_owner(db, company.id, current_user_id)

            update_data = company_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(company, field, value)

            updated_company = await company_repository.update_one(db, company)
            logger.info(f"Company updated: {company.name} (ID: {company.id})")
            return updated_company

        except PermissionDeniedException:
            raise
        except Exception as e:
            logger.error(f"Error updating company {company.id}: {str(e)}")
            raise ServiceException("Failed to update company")

    async def delete_company(
        self, db: AsyncSession, company: Company, current_user_id: int
    ) -> None:
        """
        Delete company.
        Only owner can delete the company.
        """
        try:
            await permission_service.require_owner(db, company.id, current_user_id)

            await company_repository.delete_one(db, company)
            logger.info(f"Company deleted: {company.name} (ID: {company.id})")

        except PermissionDeniedException:
            raise
        except Exception as e:
            logger.error(f"Error deleting company {company.id}: {str(e)}")
            raise ServiceException("Failed to delete company")

    async def get_user_companies(
        self, db: AsyncSession, owner_id: int, skip: int, limit: int
    ) -> tuple[list[Company], int]:
        """
        Get all companies owned by a specific user.
        """
        try:
            return await company_repository.get_by_owner(db, owner_id, skip, limit)
        except Exception as e:
            logger.error(f"Error fetching companies for user {owner_id}: {str(e)}")
            raise ServiceException("Failed to retrieve user companies")


company_service = CompanyService()
