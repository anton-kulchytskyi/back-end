"""Pydantic schemas for Request model."""

from pydantic import BaseModel

from app.schemas.base import InvitationRequestResponse


class RequestCreateRequest(BaseModel):
    """Request schema for creating membership request (User requests to join)."""

    company_id: int  # User specifies which company to join


class RequestResponse(InvitationRequestResponse):
    """
    Request response schema with all fields.

    Inherits from InvitationRequestResponse:
    - id, company_id, user_id, status, created_at, updated_at
    """

    pass  # All fields inherited from base


class RequestsListResponse(BaseModel):
    """Paginated list of membership requests."""

    requests: list[RequestResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
