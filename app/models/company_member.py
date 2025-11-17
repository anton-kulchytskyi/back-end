from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.enums.role import Role
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
    role: Mapped[Role] = mapped_column(
        SQLEnum(
            Role,
            name="role_enum",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default="member",
        index=True,
    )
    company: Mapped["Company"] = relationship("Company", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="company_memberships")

    def __repr__(self) -> str:
        return f"<CompanyMember(company_id={self.company_id}, user_id={self.user_id}, role={self.role})>"
