from app.core.exceptions import NotFoundException, ServiceException
from app.core.logger import logger
from app.core.unit_of_work import AbstractUnitOfWork
from app.enums.role import Role
from app.models.company import Company
from app.models.company_member import CompanyMember
from app.schemas.company import CompanyCreateRequest, CompanyUpdateRequest
from app.services.permission_service import PermissionService


class CompanyService:
    """Service layer for company operations."""

    def __init__(self, uow: AbstractUnitOfWork, permission_service: PermissionService):
        self._uow = uow
        self._permission_service = permission_service

    async def create_company(
        self, company_data: CompanyCreateRequest, owner_id: int
    ) -> Company:
        """
        Create a new company and assign creator as owner.
        """
        async with self._uow:
            try:
                company = Company(
                    name=company_data.name,
                    description=company_data.description,
                    owner_id=owner_id,
                    is_visible=True,
                )
                created_company = await self._uow.companies.create_one(company)

                member = CompanyMember(
                    company_id=created_company.id, user_id=owner_id, role=Role.OWNER
                )
                await self._uow.company_member.create_one(member)

                await self._uow.commit()

                logger.info(
                    f"Company created: {created_company.name} (ID: {created_company.id}) by user {owner_id}"
                )
                return created_company

            except Exception as e:
                logger.error(f"Error creating company: {str(e)}")
                raise ServiceException("Failed to create company")

    async def get_all_companies(
        self, skip: int, limit: int
    ) -> tuple[list[Company], int]:
        """
        Get all companies (paginated).
        """
        async with self._uow:
            try:
                return await self._uow.companies.get_visible_companies(skip, limit)

            except Exception as e:
                logger.error(f"Error fetching companies: {str(e)}")
                raise ServiceException("Failed to retrieve companies")

    async def get_company_by_id(self, company_id: int) -> Company:
        """
        Get company by ID.
        """
        async with self._uow:
            try:
                company = await self._uow.companies.get_one_by_id(company_id)
                if not company:
                    raise NotFoundException(f"Company with ID {company_id} not found")
                return company

            except NotFoundException:
                raise
            except Exception as e:
                logger.error(f"Error fetching company {company_id}: {str(e)}")
                raise ServiceException("Failed to retrieve company")

    async def update_company(
        self,
        company: Company,
        company_data: CompanyUpdateRequest,
        current_user_id: int,
    ) -> Company:
        """
        Update company information.
        Only owner can update the company.
        """
        await self._permission_service.require_owner(company.id, current_user_id)
        async with self._uow:
            try:
                update_data = company_data.model_dump(exclude_unset=True)
                for field, value in update_data.items():
                    setattr(company, field, value)

                updated_company = await self._uow.companies.update_one(company)
                await self._uow.commit()
                logger.info(f"Company updated: {company.name} (ID: {company.id})")
                return updated_company

            except Exception as e:
                logger.error(f"Error updating company {company.id}: {str(e)}")
                raise ServiceException("Failed to update company")

    async def delete_company(self, company: Company, current_user_id: int) -> None:
        """
        Delete company.
        Only owner can delete the company.
        """
        await self._permission_service.require_owner(company.id, current_user_id)
        async with self._uow:
            try:
                await self._uow.companies.delete_one(company)
                await self._uow.commit()
                logger.info(f"Company deleted: {company.name} (ID: {company.id})")

            except Exception as e:
                logger.error(f"Error deleting company {company.id}: {str(e)}")
                raise ServiceException("Failed to delete company")

    async def get_user_companies(
        self, owner_id: int, skip: int, limit: int
    ) -> tuple[list[Company], int]:
        """
        Get all companies owned by a specific user.
        """
        async with self._uow:
            try:
                return await self._uow.companies.get_by_owner(owner_id, skip, limit)
            except Exception as e:
                logger.error(f"Error fetching companies for user {owner_id}: {str(e)}")
                raise ServiceException("Failed to retrieve user companies")
