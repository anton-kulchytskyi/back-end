from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base.mixins import IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models import QuizQuestion, QuizUserAnswer


class QuizAnswer(IDMixin, TimestampMixin, Base):
    """
    Answer model representing a possible answer option for a question.
    """

    __tablename__ = "quiz_answers"

    question_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    question: Mapped["QuizQuestion"] = relationship(back_populates="answers")
    user_answers: Mapped[list["QuizUserAnswer"]] = relationship(back_populates="answer")

    def __repr__(self) -> str:
        return f"<Answer(id={self.id}, question_id={self.question_id}, is_correct={self.is_correct})>"
