"""API endpoints for membership requests."""

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_user, get_request_service
from app.enums.status import Status
from app.models.user import User
from app.schemas.pagination import PaginationBaseSchema
from app.schemas.request import (
    RequestCreateRequest,
    RequestResponse,
    RequestsListResponse,
)
from app.services.companies.request_service import RequestService

router = APIRouter()


# --- User endpoints (for requests they created) --- #


@router.post(
    "",
    response_model=RequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User creates request to join company",
)
async def create_request(
    request_data: RequestCreateRequest,
    current_user: User = Depends(get_current_user),
    request_service: RequestService = Depends(get_request_service),
):
    """
    User creates request to join company.

    - **company_id**: ID of company to join

    **Permissions**: Authenticated user
    """
    request = await request_service.create_request(
        request_data.company_id, current_user.id
    )
    return RequestResponse.model_validate(request)


@router.delete(
    "/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="User cancels own request",
)
async def cancel_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    request_service: RequestService = Depends(get_request_service),
):
    """
    User cancels own pending request.

    - **request_id**: Request ID

    **Permissions**: Request creator only
    """
    await request_service.cancel_request(request_id, current_user.id)


@router.get(
    "/me",
    response_model=RequestsListResponse,
    summary="User views sent requests",
)
async def get_my_requests(
    pagination: PaginationBaseSchema = Depends(),
    status_filter: Status | None = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    request_service: RequestService = Depends(get_request_service),
):
    """
    User views requests they created.

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10, max: 100)
    - **status**: Optional filter (pending/accepted/declined)

    **Permissions**: Authenticated user
    """
    return await request_service.get_user_requests_paginated(
        user_id=current_user.id,
        pagination=pagination,
        status=status_filter,
    )
