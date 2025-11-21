from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, relationship

from app.core.database import Base
from app.models.mixins import IDMixin, InvitationRequestMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.user import User


class Invitation(IDMixin, TimestampMixin, InvitationRequestMixin, Base):
    """
    Invitation model for company invitations.

    Owner invites User to join company.
    User can accept or decline.
    """

    __tablename__ = "invitations"

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="invitations")
    user: Mapped["User"] = relationship("User", back_populates="invitations")

    def __repr__(self) -> str:
        return f"<Invitation(company_id={self.company_id}, user_id={self.user_id}, status={self.status})>"
