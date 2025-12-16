from app.core.exceptions import BadRequestException, NotFoundException, ServiceException
from app.core.logger import logger
from app.core.unit_of_work import AbstractUnitOfWork
from app.schemas.quiz.quiz_export import QuizAnswerExportData
from app.services.companies.permission_service import PermissionService
from app.services.quiz.quiz_service import QuizService


class QuizExportService:
    """Service for exporting quiz data from Redis."""

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        permission_service: PermissionService,
        quiz_service: QuizService,
    ):
        self._uow = uow
        self._permissions = permission_service
        self._quiz_service = quiz_service

    async def export_user_data(
        self,
        user_id: int,
        quiz_id: int | None = None,
    ) -> list[QuizAnswerExportData]:
        """Export current user's quiz their own quiz results/answers"""

        async with self._uow:
            try:
                attempts = await self._uow.quiz_attempt.get_answers_for_export(
                    user_id=user_id,
                    quiz_id=quiz_id,
                )

                return self._map_attempts_to_answers(attempts)
            except Exception as e:
                logger.error(
                    "Failed to export user %s data: %s",
                    user_id,
                    e,
                    extra={"user_id": user_id},
                    exc_info=True,
                )
                raise ServiceException("Failed to export user data")

    async def export_company_data(
        self,
        company_id: int,
        current_user_id: int,
        user_id: int | None = None,
        quiz_id: int | None = None,
    ) -> list[QuizAnswerExportData]:
        """
        Export quiz results for a whole company.
        Only allowed for: company owner + company admins.
        """

        await self._permissions.require_admin(company_id, current_user_id)

        async with self._uow:
            try:
                if quiz_id:
                    quiz = await self._quiz_service.get_quiz_for_user(quiz_id)
                    if quiz.company_id != company_id:
                        raise BadRequestException(
                            f"Quiz {quiz_id} does not belong to company {company_id}"
                        )

                attempts = await self._uow.quiz_attempt.get_answers_for_export(
                    company_id=company_id,
                    user_id=user_id,
                    quiz_id=quiz_id,
                )

                return self._map_attempts_to_answers(attempts)

            except NotFoundException:
                raise
            except Exception as e:
                logger.error(
                    "Failed to export company %s data: %s",
                    company_id,
                    e,
                    extra={"company_id": company_id},
                    exc_info=True,
                )
                raise ServiceException("Failed to export company data")

    @staticmethod
    def _map_attempts_to_answers(attempts) -> list[QuizAnswerExportData]:
        results: list[QuizAnswerExportData] = []

        for attempt in attempts:
            for answer in attempt.user_answers:
                results.append(
                    QuizAnswerExportData(
                        user_id=attempt.user_id,
                        company_id=attempt.company_id,
                        quiz_id=attempt.quiz_id,
                        attempt_id=attempt.id,
                        question_id=answer.question_id,
                        answer_id=answer.answer_id,
                        is_correct=answer.is_correct,
                        answered_at=answer.answered_at,
                    )
                )

        return results
