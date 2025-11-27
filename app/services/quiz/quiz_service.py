from app.core.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    ServiceException,
)
from app.core.logger import logger
from app.core.unit_of_work import AbstractUnitOfWork
from app.models import Quiz, QuizAnswer, QuizQuestion, User
from app.schemas import (
    PaginationBaseSchema,
    QuizCreateRequest,
    QuizQuestionCreateRequest,
    QuizResponse,
    QuizUpdateRequest,
    QuizzesListResponse,
)
from app.services import PermissionService
from app.utils.nested import replace_children
from app.utils.pagination import paginate_query


class QuizService:
    """Service for quiz operations (Quiz + Questions + Answers as one aggregate)."""

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        permission_service: PermissionService,
    ):
        self._uow = uow
        self._permission_service = permission_service

    async def create_quiz(
        self,
        company_id: int,
        current_user: User,
        data: QuizCreateRequest,
    ) -> Quiz:
        """
        Create quiz with questions and answers.

        Only for owner/admin of company.

        """
        await self._permission_service.require_admin(company_id, current_user.id)

        async with self._uow:
            try:
                quiz = Quiz(
                    title=data.title,
                    description=data.description,
                    company_id=company_id,
                    created_by=current_user.id,
                )
                created_quiz = await self._uow.quiz.create_one(quiz)

                await self._create_questions_with_answers(created_quiz, data.questions)

                await self._uow.commit()

                await self._uow.quiz.refresh_after_create_or_update(created_quiz)

                return await self._uow.quiz.get_with_relations(created_quiz.id)
            except Exception as e:
                logger.error(f"Error creating quiz: {str(e)}")
                raise ServiceException("Failed to create quiz")

    async def get_quiz(self, quiz_id: int, current_user: User) -> Quiz:
        """
        Get quiz with all relations (questions + answers with is_correct).

        For owner/admin use - shows correct answers.
        """
        async with self._uow:
            try:
                return await self._get_quiz_with_permission_check(quiz_id, current_user)
            except (NotFoundException, PermissionDeniedException):
                raise
            except Exception as e:
                logger.error(f"Error fetching quiz {quiz_id}: {str(e)}")
                raise ServiceException("Failed to retrieve quiz")

    async def get_quiz_for_user(self, quiz_id: int) -> Quiz:
        """
        Get quiz for user taking the quiz (public version).
        """
        async with self._uow:
            try:
                return await self._get_quiz_no_permissions(quiz_id)
            except NotFoundException:
                raise
            except Exception as e:
                logger.error(f"Error fetching quiz {quiz_id}: {str(e)}")
                raise ServiceException("Failed to retrieve quiz")

    async def get_company_quizzes_paginated(
        self,
        company_id: int,
        pagination: PaginationBaseSchema,
    ) -> QuizzesListResponse:
        """
        Get paginated list of quizzes for a company using unified pagination.
        """
        async with self._uow:
            try:

                async def db_fetch(skip: int, limit: int):
                    return await self._uow.quiz.get_by_company(
                        company_id=company_id,
                        skip=skip,
                        limit=limit,
                    )

                return await paginate_query(
                    db_fetch_func=db_fetch,
                    pagination=pagination,
                    response_schema=QuizzesListResponse,
                    item_schema=QuizResponse,
                )
            except Exception as e:
                logger.error(
                    f"Error fetching paginated quizzes for company {company_id}: {e}"
                )
                raise ServiceException("Failed to retrieve company's quizzes")

    async def update_quiz(
        self,
        quiz_id: int,
        current_user: User,
        data: QuizUpdateRequest,
    ) -> Quiz:
        """
        Update quiz (title, description, questions).

        Only for owner/admin of company.
        """
        quiz = await self._get_quiz_with_permission_check(quiz_id, current_user)
        async with self._uow:
            try:
                update_data = data.model_dump(exclude_unset=True)
                if "title" in update_data:
                    quiz.title = update_data["title"]
                if "description" in update_data:
                    quiz.description = update_data["description"]

                await self._uow.quiz.update_one(quiz)

                if data.questions is not None:
                    await replace_children(
                        session=self._uow.session,
                        child_model=QuizQuestion,
                        parent_id_field=QuizQuestion.quiz_id,
                        parent_id=quiz_id,
                        new_children_data=data.questions,
                        create_child_func=lambda q: self._build_question_with_answers(
                            quiz, q
                        ),
                    )

                await self._uow.commit()

                await self._uow.quiz.refresh_after_create_or_update(quiz)

                return await self._uow.quiz.get_with_relations(quiz_id)
            except Exception as e:
                logger.error(f"Error updating quiz {quiz_id}: {str(e)}")
                raise ServiceException("Failed to update quiz")

    async def delete_quiz(
        self,
        quiz_id: int,
        current_user: User,
    ) -> None:
        """
        Delete quiz (CASCADE will delete questions and answers).
        Only for owner/admin of company.
        """
        quiz = await self._get_quiz_with_permission_check(quiz_id, current_user)
        async with self._uow:
            try:
                await self._uow.quiz.delete_one(quiz)

                await self._uow.commit()

                logger.info(
                    f"Quiz {quiz_id} deleted by user {current_user.id} "
                    f"from company {quiz.company_id}"
                )
            except Exception as e:
                logger.error(f"Error deleting quiz {quiz_id}: {str(e)}")
                raise ServiceException("Failed to delete quiz")

    async def _get_quiz_no_permissions(self, quiz_id: int) -> Quiz:
        quiz = await self._uow.quiz.get_with_relations(quiz_id)

        if not quiz:
            raise NotFoundException(f"Quiz with id {quiz_id} not found")

        return quiz

    async def _get_quiz_with_permission_check(
        self,
        quiz_id: int,
        current_user: User,
    ) -> Quiz:
        quiz = await self._get_quiz_no_permissions(quiz_id)

        await self._permission_service.require_admin(quiz.company_id, current_user.id)

        return quiz

    def _build_question_with_answers(
        self, quiz: Quiz, q: QuizQuestionCreateRequest
    ) -> QuizQuestion:
        """
        Build Question + nested Answers ORM objects.
        Used inside replace_children().
        """
        question = QuizQuestion(quiz_id=quiz.id, title=q.title)

        question.answers = [
            QuizAnswer(text=answer.text, is_correct=answer.is_correct)
            for answer in q.answers
        ]

        return question

    async def _create_questions_with_answers(
        self, quiz: Quiz, questions_data: list[QuizQuestionCreateRequest]
    ):
        """
        Initial creation of questions + answers.
        """
        for q in questions_data:
            question = self._build_question_with_answers(quiz, q)
            await self._uow.quiz_question.create_one(question)

        await self._uow.session.flush()
