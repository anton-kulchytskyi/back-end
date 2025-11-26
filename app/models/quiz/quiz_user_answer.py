from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base.mixins import IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models import QuizAnswer, QuizAttempt, QuizQuestion


class QuizUserAnswer(IDMixin, TimestampMixin, Base):
    """
    UserAnswer model representing a user's answer to a specific question.

    This table stores detailed information about each answer within an attempt.
    """

    __tablename__ = "quiz_user_answers"

    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False
    )
    answer_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_answers.id", ondelete="CASCADE"), nullable=False
    )

    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    attempt: Mapped["QuizAttempt"] = relationship(back_populates="user_answers")
    question: Mapped["QuizQuestion"] = relationship(back_populates="user_answers")
    answer: Mapped["QuizAnswer"] = relationship(back_populates="user_answers")

    __table_args__ = UniqueConstraint(
        "attempt_id", "question_id", name="uq_attempt_question"
    )

    def __repr__(self) -> str:
        return (
            f"<UserAnswer(id={self.id}, attempt_id={self.attempt_id}, "
            f"question_id={self.question_id}, is_correct={self.is_correct})>"
        )
