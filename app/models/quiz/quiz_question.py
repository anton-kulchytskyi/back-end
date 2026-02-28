from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base.mixins import IDMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models import Quiz, QuizAnswer, QuizUserAnswer


class QuizQuestion(IDMixin, TimestampMixin, Base):
    """
    Question model representing a question within a quiz.
    """

    __tablename__ = "quiz_questions"

    quiz_id: Mapped[int] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)

    quiz: Mapped["Quiz"] = relationship(back_populates="questions")
    answers: Mapped[list["QuizAnswer"]] = relationship(
        back_populates="question", cascade="all, delete-orphan", lazy="selectin"
    )
    user_answers: Mapped[list["QuizUserAnswer"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )

    @property
    def correct_answers_count(self) -> int:
        """Return the number of correct answers for this question."""
        return sum(1 for answer in self.answers if answer.is_correct)

    def __repr__(self) -> str:
        return f"<Question(id={self.id}, quiz_id={self.quiz_id}, title='{self.title[:50]}...')>"
