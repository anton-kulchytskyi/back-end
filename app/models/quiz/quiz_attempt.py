from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.base.mixins import IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models import Company, Quiz, QuizUserAnswer, User


class QuizAttempt(IDMixin, TimestampMixin, Base):
    """
    QuizAttempt model representing a single quiz attempt by a user.

    This is the main table for analytics and results storage.
    Each row represents one complete quiz attempt with results.
    """

    __tablename__ = "quiz_attempts"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    quiz_id: Mapped[int] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )

    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="quiz_attempts")
    quiz: Mapped["Quiz"] = relationship(back_populates="attempts")
    company: Mapped["Company"] = relationship(back_populates="quiz_attempts")
    user_answers: Mapped[list["QuizUserAnswer"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_user_completed", "user_id", "completed_at"),
        Index("idx_company_completed", "company_id", "completed_at"),
        Index("idx_quiz_completed", "quiz_id", "completed_at"),
        Index("idx_user_company_quiz", "user_id", "company_id", "quiz_id"),
    )

    @property
    def percentage_score(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return (self.score / self.total_questions) * 100.0

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None

    def calculate_score(self) -> int:
        return sum(1 for ua in self.user_answers if ua.is_correct)

    def mark_completed(self) -> None:
        self.completed_at = datetime.now(timezone.utc)
        self.score = self.calculate_score()

    def __repr__(self) -> str:
        return (
            f"<QuizAttempt(id={self.id}, user_id={self.user_id}, quiz_id={self.quiz_id}, "
            f"score={self.score}/{self.total_questions}, completed={self.is_completed})>"
        )
