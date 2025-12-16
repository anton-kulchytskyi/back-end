from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.enums.notification_status import NotificationStatus
from app.models.base.mixins import IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models import User


class Notification(IDMixin, TimestampMixin, Base):
    """
    Notification model for user notifications.

    Attributes:
        id: Primary key (from IDMixin)
        user_id: Foreign key to users table
        message: Notification message text
        status: Read status from emun NotificationStatus (default: UNREAD)
        created_at: Creation timestamp (from TimestampMixin)
        updated_at: Last update timestamp (from TimestampMixin)

        user: Relationship to User model
    """

    __tablename__ = "notifications"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        SQLEnum(
            NotificationStatus,
            name="notification_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        default=NotificationStatus.UNREAD,
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, user_id={self.user_id}, status={self.status.value})>"
