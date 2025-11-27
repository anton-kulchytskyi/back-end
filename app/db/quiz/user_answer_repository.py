from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base.base_repository import BaseRepository
from app.models import QuizUserAnswer


class QuizUserAnswerRepository(BaseRepository[QuizUserAnswer]):
    """Repository for QuizUserAnswer model."""

    def __init__(self, session: AsyncSession):
        super().__init__(model=QuizUserAnswer, session=session)

    async def bulk_create_answers(
        self,
        answers_data: list[dict],
    ) -> list[QuizUserAnswer]:
        """
        Bulk create multiple user answers.

        Args:
            answers_data: List of dicts with keys:
                attempt_id, question_id, answer_id, is_correct

        Returns:
            List of created QuizUserAnswer objects
        """
        user_answers = [
            QuizUserAnswer(
                attempt_id=data["attempt_id"],
                question_id=data["question_id"],
                answer_id=data["answer_id"],
                is_correct=data["is_correct"],
            )
            for data in answers_data
        ]

        self.session.add_all(user_answers)
        await self.session.flush()

        return user_answers

    #     )
