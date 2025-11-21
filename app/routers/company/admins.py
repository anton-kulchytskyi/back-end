from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_admin_service, get_current_user
from app.schemas.member import CompanyMemberResponse, CompanyMembersListResponse

router = APIRouter()


@router.get("", response_model=CompanyMembersListResponse)
async def list_admins(
    company_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    admin_service=Depends(get_admin_service),
    current_user=Depends(get_current_user),
):
    admins, total = await admin_service.get_admins(
        current_user_id=current_user.id,
        company_id=company_id,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    return CompanyMembersListResponse(
        members=admins,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{user_id}", response_model=CompanyMemberResponse)
async def appoint_admin(
    company_id: int,
    user_id: int,
    admin_service=Depends(get_admin_service),
    current_user=Depends(get_current_user),
):
    return await admin_service.appoint_admin(
        company_id=company_id,
        target_user_id=user_id,
        current_user_id=current_user.id,
    )


@router.delete("/{user_id}", response_model=CompanyMemberResponse)
async def remove_admin(
    company_id: int,
    user_id: int,
    admin_service=Depends(get_admin_service),
    current_user=Depends(get_current_user),
):
    return await admin_service.remove_admin(
        company_id=company_id,
        target_user_id=user_id,
        current_user_id=current_user.id,
    )
