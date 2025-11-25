from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base.mixins import IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models import Company, QuizAttempt, QuizQuestion, User


class Quiz(IDMixin, TimestampMixin, Base):
    """
    Quiz model representing a quiz within a company.
    """

    __tablename__ = "quizzes"

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    company: Mapped["Company"] = relationship(back_populates="quizzes")
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])
    questions: Mapped[list["QuizQuestion"]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan", lazy="selectin"
    )
    attempts: Mapped[list["QuizAttempt"]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan"
    )

    @property
    def total_questions_count(self) -> int:
        return len(self.questions)

    @property
    def participation_count(self) -> int:
        return len(self.attempts)

    def __repr__(self) -> str:
        return (
            f"<Quiz(id={self.id}, title='{self.title}', company_id={self.company_id})>"
        )
