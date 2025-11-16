from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.user import User


class CompanyMember(IDMixin, TimestampMixin, Base):
    """CompanyMember model for managing user roles in companies."""

    __tablename__ = "company_members"

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="member", index=True
    )
    company: Mapped["Company"] = relationship("Company", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="company_memberships")

    def __repr__(self) -> str:
        return f"<CompanyMember(company_id={self.company_id}, user_id={self.user_id}, role={self.role})>"
