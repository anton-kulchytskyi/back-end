from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.enums.status import Status


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class IDMixin:
    id: Mapped[int] = mapped_column(primary_key=True, index=True)


class InvitationRequestMixin:
    """
    Mixin for Invitation and Request models.
    Contains common fields: company_id, user_id, status.
    """

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[Status] = mapped_column(
        SQLEnum(
            Status,
            name="status_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=Status.PENDING,
        index=True,
    )
