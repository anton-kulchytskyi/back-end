from app.core.exceptions import BadRequestException, NotFoundException, ServiceException
from app.core.logger import logger
from app.schemas.quiz.qiuz_redis import RedisQuizAnswerData
from app.services.companies.permission_service import PermissionService
from app.services.quiz.quiz_redis_service import RedisQuizService
from app.services.quiz.quiz_service import QuizService


class QuizExportService:
    """Service for exporting quiz data from Redis."""

    def __init__(
        self,
        redis_quiz_service: RedisQuizService,
        permission_service: PermissionService,
        quiz_service: QuizService,
    ):
        self._redis = redis_quiz_service
        self._permissions = permission_service
        self._quiz_service = quiz_service

    async def export_user_data(
        self,
        user_id: int,
        quiz_id: int | None = None,
    ) -> list[RedisQuizAnswerData]:
        """Export current user's quiz attempts from Redis."""

        try:
            logger.info(
                "Exporting Redis quiz data for user %s",
                user_id,
                extra={"user_id": user_id, "quiz_id": quiz_id},
            )

            if quiz_id:
                try:
                    await self._quiz_service.get_quiz_for_user(quiz_id)
                except NotFoundException:
                    logger.warning(
                        "Quiz %s not found; continuing with Redis export",
                        quiz_id,
                        extra={"quiz_id": quiz_id},
                    )

            answers = await self._redis.fetch_answers(
                user_id=user_id,
                quiz_id=quiz_id,
                company_id=None,
            )

            logger.info(
                "Exported %s answers for user %s",
                len(answers),
                user_id,
                extra={"user_id": user_id},
            )

            return answers

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
    ) -> list[RedisQuizAnswerData]:
        """
        Export quiz results for a whole company.
        Only allowed for: company owner + company admins.
        """

        await self._permissions.require_admin(company_id, current_user_id)

        try:
            logger.info(
                "Company export requested",
                extra={
                    "company_id": company_id,
                    "requested_by": current_user_id,
                    "user_filter": user_id,
                    "quiz_filter": quiz_id,
                },
            )

            if quiz_id:
                quiz = await self._quiz_service.get_quiz_for_user(quiz_id)
                if quiz.company_id != company_id:
                    raise BadRequestException(
                        f"Quiz {quiz_id} does not belong to company {company_id}"
                    )

            answers = await self._redis.fetch_answers(
                user_id=user_id,
                company_id=company_id,
                quiz_id=quiz_id,
            )

            logger.info(
                "Exported %s company answers",
                len(answers),
                extra={
                    "company_id": company_id,
                    "count": len(answers),
                    "user_filter": user_id,
                    "quiz_filter": quiz_id,
                },
            )

            return answers

        except (NotFoundException, BadRequestException):
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
