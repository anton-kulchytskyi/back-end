from pydantic import BaseModel, EmailStr

from app.schemas.base import InvitationRequestResponse
from app.schemas.pagination import PaginatedResponseBaseSchema


class InvitationCreateRequest(BaseModel):
    """Request schema for creating invitation (Owner sends invitation)."""

    user_email: EmailStr  # Owner specifies user by email


class InvitationResponse(InvitationRequestResponse):
    """
    Invitation response schema with all fields.

    Inherits from InvitationRequestResponse:
    - id, company_id, user_id, status, created_at, updated_at
    """

    pass  # All fields inherited from base


class InvitationsListResponse(PaginatedResponseBaseSchema[InvitationResponse]):
    """Unified paginated response for invitations."""

    pass  # All fields inherited from pagination
