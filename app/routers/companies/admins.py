from fastapi import APIRouter, Depends

from app.core.dependencies import get_admin_service, get_current_user
from app.schemas.member import CompanyMemberResponse, CompanyMembersListResponse
from app.schemas.pagination import PaginationBaseSchema

router = APIRouter()


@router.get(
    "",
    response_model=CompanyMembersListResponse,
    summary="List company admins",
    tags=["Companies - Admins"],
)
async def list_admins(
    company_id: int,
    pagination: PaginationBaseSchema = Depends(),
    admin_service=Depends(get_admin_service),
    current_user=Depends(get_current_user),
):
    """
    Get paginated list of company administrators.

    Permissions: Any company member
    """
    return await admin_service.get_admins_paginated(
        current_user_id=current_user.id,
        company_id=company_id,
        pagination=pagination,
    )


@router.post(
    "/{user_id}",
    response_model=CompanyMemberResponse,
    summary="Appoint admin",
    tags=["Companies - Admins"],
)
async def appoint_admin(
    company_id: int,
    user_id: int,
    admin_service=Depends(get_admin_service),
    current_user=Depends(get_current_user),
):
    """
    Promote company member to admin role. Target user must already be a company member.

    **Permissions**: Owner only
    """
    return await admin_service.appoint_admin(
        company_id=company_id,
        target_user_id=user_id,
        current_user_id=current_user.id,
    )


@router.delete(
    "/{user_id}",
    response_model=CompanyMemberResponse,
    summary="Remove admin",
    tags=["Companies - Admins"],
)
async def remove_admin(
    company_id: int,
    user_id: int,
    admin_service=Depends(get_admin_service),
    current_user=Depends(get_current_user),
):
    """
    Demote admin to regular member. Admin role is removed, user remains as member.

    **Permissions**: Owner only
    """
    return await admin_service.remove_admin(
        company_id=company_id,
        target_user_id=user_id,
        current_user_id=current_user.id,
    )
