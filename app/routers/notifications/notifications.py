from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user, get_notification_service
from app.models import User
from app.schemas import (
    MarkAllAsReadResponse,
    MarkAsReadResponse,
    NotificationsListResponse,
    NotificationsPaginationRequest,
)
from app.services import NotificationService

router = APIRouter()


@router.get(
    "",
    response_model=NotificationsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user notifications",
    description="Get paginated list of notifications for the current user with optional filter for unread only.",
)
async def get_my_notifications(
    pagination: NotificationsPaginationRequest = Depends(),
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationsListResponse:
    """Get paginated notifications for the current user."""

    return await notification_service.get_user_notifications(
        user_id=current_user.id,
        pagination=pagination,
    )


@router.put(
    "/{notification_id}/read",
    response_model=MarkAsReadResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark notification as read",
    description="Mark a specific notification as read. Users can only mark their own notifications.",
)
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> MarkAsReadResponse:
    """
    Mark a specific notification as read.

    - **notification_id**: ID of the notification to mark as read

    Permission: Users can only mark their own notifications as read.
    """
    return await notification_service.mark_notification_as_read(
        notification_id=notification_id,
        user_id=current_user.id,
    )


@router.put(
    "/read-all",
    response_model=MarkAllAsReadResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark all notifications as read",
    description="Mark all unread notifications as read for the current user.",
)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> MarkAllAsReadResponse:
    """
    Mark all unread notifications as read for the current user.

    Returns the count of notifications that were marked as read.
    """
    return await notification_service.mark_all_as_read(user_id=current_user.id)
