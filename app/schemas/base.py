from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums.status import Status


class InvitationRequestBase(BaseModel):
    """Base schema for Invitation and Request - common fields."""

    company_id: int
    user_id: int
    status: Status


class InvitationRequestResponse(InvitationRequestBase):
    """
    Base response schema for Invitation and Request.

    Add id and timestamps to base fields.
    """

    id: int
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
