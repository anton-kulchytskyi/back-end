from datetime import datetime, timezone

from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    PermissionDeniedException,
    ServiceException,
)
from app.core.logger import logger
from app.core.unit_of_work import AbstractUnitOfWork
from app.models import Quiz, User
from app.schemas import (
    PaginationBaseSchema,
    QuizAttemptResponse,
    QuizAttemptsListResponse,
    QuizAttemptSubmitRequest,
    RedisQuizAnswerData,
    UserQuizStatisticsResponse,
)
from app.services.companies.permission_service import PermissionService
from app.services.quiz.quiz_redis_service import RedisQuizService
from app.services.quiz.quiz_service import QuizService
from app.utils.pagination import paginate_query


class QuizAttemptService:
    """Service for quiz attempt operations."""

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        permission_service: PermissionService,
        quiz_service: QuizService,
        redis_quiz_service: RedisQuizService,
    ):
        self._uow = uow
        self._permisson_service = permission_service
        self._quiz_service = quiz_service
        self._redis_quiz_service = redis_quiz_service

    async def submit_quiz_attempt(
        self,
        quiz_id: int,
        current_user: User,
        data: QuizAttemptSubmitRequest,
    ) -> QuizAttemptResponse:
        """
        Submit quiz attempt with answers.

        User can take quiz from any visible company.

        Steps:
        1. Get quiz with company (eager loaded)
        2. Validate company is visible
        3. Validate all answers
        4. Create attempt
        5. Create user answers
        6. Calculate score and mark completed
        7. Return response
        """
        async with self._uow:
            try:
                quiz = await self._quiz_service.get_quiz_for_user(quiz_id)

                if not quiz.company.is_visible:
                    await self._permisson_service.require_admin(
                        quiz.company_id, current_user.id
                    )

                self._validate_quiz_answers(quiz, data)

                attempt = await self._uow.quiz_attempt.create_attempt(
                    user_id=current_user.id,
                    quiz_id=quiz_id,
                    company_id=quiz.company_id,
                    total_questions=len(quiz.questions),
                )

                answers_data = []
                redis_payloads = []
                for user_answer in data.answers:
                    question = self._find_question(quiz, user_answer.question_id)
                    selected_answer = self._find_answer(question, user_answer.answer_id)

                    answers_data.append(
                        {
                            "attempt_id": attempt.id,
                            "question_id": user_answer.question_id,
                            "answer_id": user_answer.answer_id,
                            "is_correct": selected_answer.is_correct,
                        }
                    )

                    redis_payloads.append(
                        RedisQuizAnswerData(
                            user_id=current_user.id,
                            company_id=quiz.company_id,
                            quiz_id=quiz_id,
                            question_id=user_answer.question_id,
                            answer_id=user_answer.answer_id,
                            is_correct=selected_answer.is_correct,
                            attempt_id=attempt.id,
                            answered_at=datetime.now(timezone.utc),
                        )
                    )

                await self._uow.quiz_user_answer.bulk_create_answers(answers_data)

                await self._uow.session.refresh(attempt, ["user_answers"])
                attempt.mark_completed()

                await self._uow.commit()

                completed_attempt = await self._uow.quiz_attempt.get_with_details(
                    attempt.id
                )

                if self._redis_quiz_service:
                    for p in redis_payloads:
                        await self._redis_quiz_service.save_answer(p)

                return QuizAttemptResponse.model_validate(completed_attempt)

            except (
                NotFoundException,
                PermissionDeniedException,
                BadRequestException,
            ):
                raise
            except Exception as e:
                logger.error(
                    f"Error submitting quiz attempt for quiz {quiz_id}: {str(e)}"
                )
                raise ServiceException("Failed to submit quiz attempt")

    async def get_user_statistics(
        self,
        current_user: User,
        company_id: int | None = None,
    ) -> UserQuizStatisticsResponse:
        """
        Get user's quiz statistics.

        If company_id provided, includes company-specific average.
        Always includes global average across all companies.
        """
        async with self._uow:
            try:
                global_average = (
                    await self._uow.quiz_attempt.calculate_user_global_average(
                        current_user.id
                    )
                )

                company_average = None
                if company_id is not None:
                    company_average = (
                        await self._uow.quiz_attempt.calculate_user_company_average(
                            current_user.id, company_id
                        )
                    )

                total_quizzes_taken = (
                    await self._uow.quiz_attempt.count_user_completed_attempts(
                        current_user.id,
                        company_id=company_id,
                    )
                )

                last_attempt_at = await self._uow.quiz_attempt.get_user_last_attempt(
                    current_user.id
                )

                return UserQuizStatisticsResponse(
                    global_average=global_average,
                    company_average=company_average,
                    total_quizzes_taken=total_quizzes_taken,
                    last_attempt_at=last_attempt_at,
                )

            except Exception as e:
                logger.error(
                    f"Error fetching statistics for user {current_user.id}: {str(e)}"
                )
                raise ServiceException("Failed to retrieve user statistics")

    async def get_user_quiz_history(
        self,
        current_user: User,
        pagination: PaginationBaseSchema,
        company_id: int | None = None,
        quiz_id: int | None = None,
    ) -> QuizAttemptsListResponse:
        """
        Get paginated list of user's quiz attempts.

        Can be filtered by company_id and/or quiz_id.
        """
        async with self._uow:
            try:

                async def db_fetch(skip: int, limit: int):
                    return await self._uow.quiz_attempt.get_user_attempts_paginated(
                        user_id=current_user.id,
                        skip=skip,
                        limit=limit,
                        company_id=company_id,
                        quiz_id=quiz_id,
                    )

                return await paginate_query(
                    db_fetch_func=db_fetch,
                    pagination=pagination,
                    response_schema=QuizAttemptsListResponse,
                    item_schema=QuizAttemptResponse,
                )

            except Exception as e:
                logger.error(
                    f"Error fetching quiz history for user {current_user.id}: {str(e)}"
                )
                raise ServiceException("Failed to retrieve quiz history")

    def _validate_quiz_answers(
        self,
        quiz: Quiz,
        data: QuizAttemptSubmitRequest,
    ) -> None:
        """
        Validate that:
        1. User answered all questions
        2. All question_ids belong to this quiz
        3. All answer_ids belong to their respective questions
        4. No duplicate question answers
        """
        if len(data.answers) != len(quiz.questions):
            raise BadRequestException(
                f"Must answer all {len(quiz.questions)} questions. "
                f"Received {len(data.answers)} answers."
            )

        valid_question_ids = {q.id for q in quiz.questions}

        answered_question_ids = [a.question_id for a in data.answers]
        if len(answered_question_ids) != len(set(answered_question_ids)):
            raise BadRequestException("Cannot answer the same question multiple times")

        # Validate each answer belongs to quiz
        for user_answer in data.answers:
            if user_answer.question_id not in valid_question_ids:
                raise BadRequestException(
                    f"Question {user_answer.question_id} does not belong to this quiz"
                )

            question = self._find_question(quiz, user_answer.question_id)
            valid_answer_ids = {a.id for a in question.answers}

            if user_answer.answer_id not in valid_answer_ids:
                raise BadRequestException(
                    f"Answer {user_answer.answer_id} does not belong to "
                    f"question {user_answer.question_id}"
                )

    def _find_question(self, quiz: Quiz, question_id: int):
        """Find question in quiz or raise exception."""
        question = next((q for q in quiz.questions if q.id == question_id), None)
        if not question:
            raise NotFoundException(f"Question {question_id} not found in quiz")
        return question

    def _find_answer(self, question, answer_id: int):
        """Find answer in question or raise exception."""
        answer = next((a for a in question.answers if a.id == answer_id), None)
        if not answer:
            raise NotFoundException(
                f"Answer {answer_id} not found in question {question.id}"
            )
        return answer
