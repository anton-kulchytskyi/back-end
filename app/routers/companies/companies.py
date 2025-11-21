from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_company_service, get_current_user
from app.models.user import User
from app.schemas.company import (
    CompaniesListResponse,
    CompanyCreateRequest,
    CompanyResponse,
    CompanyUpdateRequest,
)
from app.services.companies.company_service import CompanyService

router = APIRouter()


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreateRequest,
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
):
    """
    Create a new company.

    The creator automatically becomes the owner of the company.
    Requires authentication.
    """
    company = await company_service.create_company(company_data, current_user.id)
    return CompanyResponse.model_validate(company)


@router.get("", response_model=CompaniesListResponse)
async def get_companies(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 10,
    company_service: CompanyService = Depends(get_company_service),
):
    """
    Get all visible companies (paginated).

    Returns only companies with is_visible=True.
    No authentication required (public endpoint).
    """
    skip = (page - 1) * page_size
    companies, total = await company_service.get_all_companies(skip, page_size)
    total_pages = (total + page_size - 1) // page_size

    return CompaniesListResponse(
        companies=[CompanyResponse.model_validate(c) for c in companies],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    company_service: CompanyService = Depends(get_company_service),
):
    """
    Get company by ID.

    No authentication required (public endpoint).
    """
    company = await company_service.get_company_by_id(company_id)
    return CompanyResponse.model_validate(company)


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    company_data: CompanyUpdateRequest,
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
):
    """
    Update company information.

    Only the company owner can update the company.
    Can update: name, description, is_visible.
    Requires authentication.
    """
    company = await company_service.get_company_by_id(company_id)
    updated_company = await company_service.update_company(
        company, company_data, current_user.id
    )
    return CompanyResponse.model_validate(updated_company)


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
):
    """
    Delete company.

    Only the company owner can delete the company.
    Also deletes all associated company_members (cascade).
    Requires authentication.
    """
    company = await company_service.get_company_by_id(company_id)
    await company_service.delete_company(company, current_user.id)
    return None
