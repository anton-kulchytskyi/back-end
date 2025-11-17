"""API endpoints for invitations."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.enums.status import Status
from app.models.user import User
from app.schemas.invitation import InvitationResponse, InvitationsListResponse
from app.services.deps import get_invitation_service
from app.services.invitation_service import InvitationService

router = APIRouter()


# --- User endpoints (for invitations they received) --- #


@router.get(
    "/me",
    response_model=InvitationsListResponse,
    summary="User views received invitations",
)
async def get_my_invitations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Status | None = Query(
        None, alias="status", description="Filter by status"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    """
    User views invitations received.

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10, max: 100)
    - **status**: Optional filter (pending/accepted/declined)

    **Permissions**: Authenticated user
    """
    skip = (page - 1) * page_size
    invitations, total = await invitation_service.get_user_invitations(
        db, current_user.id, skip, page_size, status_filter
    )

    return InvitationsListResponse(
        invitations=[InvitationResponse.model_validate(inv) for inv in invitations],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post(
    "/{invitation_id}/accept",
    response_model=InvitationResponse,
    summary="User accepts invitation",
)
async def accept_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    """
    User accepts invitation.

    Changes status to ACCEPTED and adds user as company member.

    - **invitation_id**: Invitation ID

    **Permissions**: Invited user only
    """
    invitation = await invitation_service.accept_invitation(
        db, invitation_id, current_user.id
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
    db: AsyncSession = Depends(get_db),
    invitation_service: InvitationService = Depends(get_invitation_service),
):
    """
    User declines invitation.

    Changes status to DECLINED.

    - **invitation_id**: Invitation ID

    **Permissions**: Invited user only
    """
    invitation = await invitation_service.decline_invitation(
        db, invitation_id, current_user.id
    )
    return InvitationResponse.model_validate(invitation)
