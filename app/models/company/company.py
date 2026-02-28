from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base.mixins import IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models import CompanyMember, Invitation, Quiz, QuizAttempt, Request, User


class Company(IDMixin, TimestampMixin, Base):
    """Company model for managing companies."""

    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner: Mapped["User"] = relationship("User", back_populates="owned_companies")
    members: Mapped[list["CompanyMember"]] = relationship(
        "CompanyMember", back_populates="company", cascade="all, delete-orphan"
    )
    invitations: Mapped[list["Invitation"]] = relationship(
        "Invitation",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    requests: Mapped[list["Request"]] = relationship(
        "Request", back_populates="company", cascade="all, delete-orphan"
    )
    quizzes: Mapped[list["Quiz"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )

    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name={self.name}, owner_id={self.owner_id})>"
