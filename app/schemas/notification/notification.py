from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.enums.notification_status import NotificationStatus
from app.schemas.pagination.pagination import (
    PaginatedResponseBaseSchema,
    PaginationBaseSchema,
)


class NotificationBase(BaseModel):
    """Base notification schema."""

    message: str = Field(..., description="Notification message text")


class NotificationResponse(NotificationBase):
    """Response schema for a single notification."""

    id: int = Field(..., description="Notification ID")
    status: NotificationStatus = Field(..., description="Notification status")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class NotificationsPaginationRequest(PaginationBaseSchema):
    """Pagination request for notifications list."""

    unread_only: bool = Field(
        False, description="If True, return only unread notifications"
    )


class NotificationsListResponse(PaginatedResponseBaseSchema[NotificationResponse]):
    """Paginated response schema for list of notifications."""

    unread_count: int = Field(0, description="Number of unread notifications")


class MarkAsReadResponse(BaseModel):
    id: int = Field(..., description="Notification ID")
    status: NotificationStatus = Field(..., description="Updated status")

    model_config = ConfigDict(from_attributes=True)


class MarkAllAsReadResponse(BaseModel):
    """Response schema for mark all as read operation."""

    message: str = Field(..., description="Success message")
    marked_count: int = Field(..., description="Number of notifications marked as read")
