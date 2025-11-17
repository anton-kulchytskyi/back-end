from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base
from app.models.mixins import IDMixin, InvitationRequestMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.user import User


class Request(IDMixin, TimestampMixin, InvitationRequestMixin, Base):
    """
    Request model for company membership requests.

    User requests to join company.
    Owner can accept or decline.
    """

    __tablename__ = "requests"

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="requests")
    user: Mapped["User"] = relationship("User", back_populates="requests")

    def __repr__(self) -> str:
        return f"<Request(company_id={self.company_id}, user_id={self.user_id}, status={self.status})>"
