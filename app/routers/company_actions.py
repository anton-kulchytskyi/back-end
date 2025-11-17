from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.enums.status import Status
from app.models.user import User
from app.schemas.invitation import (
    InvitationCreateRequest,
    InvitationResponse,
    InvitationsListResponse,
)
from app.schemas.request import RequestResponse, RequestsListResponse
from app.services.deps import (
    get_invitation_service,
    get_member_service,
    get_request_service,
)
from app.services.invitation_service import InvitationService
from app.services.member_service import MemberService
from app.services.request_service import RequestService

router = APIRouter()


# --- Invitation management (Owner) --- #


@router.post(
    "/{company_id}/invitations",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Owner sends invitation",
    tags=["Companies - Invitations"],
)
async def send_invitation(
    company_id: int,
    invitation_data: InvitationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    """
    Owner sends invitation to user by email.

    **Permissions**: Owner only
    """
    invitation = await invitation_service.send_invitation(
        db, company_id, invitation_data.user_email, current_user.id
    )
    return InvitationResponse.model_validate(invitation)


@router.get(
    "/{company_id}/invitations",
    response_model=InvitationsListResponse,
    summary="Owner views sent invitations",
    tags=["Companies - Invitations"],
)
async def get_company_invitations(
    company_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: Status | None = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    """
    Owner views invitations sent by company.

    **Permissions**: Owner only
    """
    skip = (page - 1) * page_size
    invitations, total = await invitation_service.get_company_invitations(
        db, company_id, current_user.id, skip, page_size, status_filter
    )

    return InvitationsListResponse(
        invitations=[InvitationResponse.model_validate(inv) for inv in invitations],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.delete(
    "/{company_id}/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Owner cancels invitation",
    tags=["Companies - Invitations"],
)
async def cancel_invitation(
    company_id: int,
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    """
    Owner cancels pending invitation.

    **Permissions**: Owner only
    """
    await invitation_service.cancel_invitation(db, invitation_id, current_user.id)


# --- Request management (Owner) --- #


@router.get(
    "/{company_id}/requests",
    response_model=RequestsListResponse,
    summary="Owner views membership requests",
    tags=["Companies - Requests"],
)
async def get_company_requests(
    company_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: Status | None = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request_service: RequestService = Depends(get_request_service),
):
    """
    Owner views membership requests to company.

    **Permissions**: Owner only
    """
    skip = (page - 1) * page_size
    requests, total = await request_service.get_company_requests(
        db, company_id, current_user.id, skip, page_size, status_filter
    )

    return RequestsListResponse(
        requests=[RequestResponse.model_validate(req) for req in requests],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post(
    "/{company_id}/requests/{request_id}/accept",
    response_model=RequestResponse,
    summary="Owner accepts membership request",
    tags=["Companies - Requests"],
)
async def accept_request(
    company_id: int,
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request_service: RequestService = Depends(get_request_service),
):
    """
    Owner accepts membership request.

    Changes status to ACCEPTED and adds user as company member.

    **Permissions**: Owner only
    """
    request = await request_service.accept_request(
        db, request_id, company_id, current_user.id
    )
    return RequestResponse.model_validate(request)


@router.post(
    "/{company_id}/requests/{request_id}/decline",
    response_model=RequestResponse,
    summary="Owner declines membership request",
    tags=["Companies - Requests"],
)
async def decline_request(
    company_id: int,
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request_service: RequestService = Depends(get_request_service),
):
    """
    Owner declines membership request.

    Changes status to DECLINED.

    **Permissions**: Owner only
    """
    request = await request_service.decline_request(
        db, request_id, company_id, current_user.id
    )
    return RequestResponse.model_validate(request)


# --- Member management (Owner) --- #


@router.delete(
    "/{company_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Owner removes member",
    tags=["Companies - Members"],
)
async def remove_member(
    company_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    member_service: MemberService = Depends(get_member_service),
):
    """
    Owner removes member from company.

    Cannot remove owner.

    **Permissions**: Owner only
    """
    await member_service.remove_member(db, company_id, user_id, current_user.id)


@router.post(
    "/{company_id}/leave",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="User leaves company",
    tags=["Companies - Members"],
)
async def leave_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    member_service: MemberService = Depends(get_member_service),
):
    """
    User leaves company.

    Owner cannot leave (must delete company or transfer ownership).

    **Permissions**: Member only (not owner)
    """
    await member_service.leave_company(db, company_id, current_user.id)
