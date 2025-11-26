from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, get_invitation_service
from app.enums import Status
from app.models import User
from app.schemas import (
    InvitationResponse,
    InvitationsListResponse,
    PaginationBaseSchema,
)
from app.services.companies.invitation_service import InvitationService

router = APIRouter()


# --- User endpoints (for invitations they received) --- #


@router.get(
    "/me",
    response_model=InvitationsListResponse,
    summary="User views received invitations",
)
async def get_my_invitations(
    pagination: PaginationBaseSchema = Depends(),
    status_filter: Status | None = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    """
    User views invitations received.

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10, max: 100)
    - **status**: Optional filter (pending/accepted/declined)

    **Permissions**: Authenticated user
    """
    return await invitation_service.get_user_invitations_paginated(
        user_id=current_user.id,
        pagination=pagination,
        status=status_filter,
    )


@router.post(
    "/{invitation_id}/accept",
    response_model=InvitationResponse,
    summary="User accepts invitation",
)
async def accept_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    """
    User accepts invitation.

    Changes status to ACCEPTED and adds user as company member.

    - **invitation_id**: Invitation ID

    **Permissions**: Invited user only
    """
    invitation = await invitation_service.accept_invitation(
        invitation_id, current_user.id
    )
    return InvitationResponse.model_validate(invitation)


@router.post(
    "/{invitation_id}/decline",
    response_model=InvitationResponse,
    summary="User declines invitation",
)
async def decline_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    """
    User declines invitation.

    Changes status to DECLINED.

    - **invitation_id**: Invitation ID

    **Permissions**: Invited user only
    """
    invitation = await invitation_service.decline_invitation(
        invitation_id, current_user.id
    )
    return InvitationResponse.model_validate(invitation)
