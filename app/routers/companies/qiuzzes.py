from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_current_user, get_quiz_service
from app.models import User
from app.schemas import (
    QuizCreateRequest,
    QuizDetailResponse,
    QuizPublicDetailResponse,
    QuizUpdateRequest,
    QuizzesListResponse,
)
from app.schemas.pagination.pagination import PaginationBaseSchema
from app.services import QuizService

router = APIRouter()


@router.post(
    "",
    response_model=QuizDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create quiz",
    description="Create a new quiz with questions and answers. Only company owner/admin can create quizzes.",
)
async def create_quiz(
    company_id: int,
    data: QuizCreateRequest,
    current_user: User = Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> QuizDetailResponse:
    """
    Create a new quiz in the company.

    **Requirements:**
    - User must be owner or admin of the company
    - Quiz must have at least 2 questions
    - Each question must have 2-4 answers
    - Each question must have at least 1 correct answer

    **Returns:**
    - Created quiz with all questions and answers
    """
    quiz = await quiz_service.create_quiz(
        company_id=company_id,
        current_user=current_user,
        data=data,
    )
    return QuizDetailResponse.model_validate(quiz)


@router.get(
    "",
    response_model=QuizzesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get company quizzes",
    description="Get paginated list of quizzes for a company.",
)
async def get_company_quizzes(
    company_id: int,
    pagination: PaginationBaseSchema = Depends(),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> QuizzesListResponse:
    """
    Get paginated list of quizzes for a company.

    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `limit`: Items per page (default: 10)

    **Returns:**
    - Paginated list of quizzes (without questions for performance)
    """
    return await quiz_service.get_company_quizzes_paginated(
        company_id=company_id,
        pagination=pagination,
    )


@router.get(
    "/{quiz_id}",
    response_model=QuizDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get quiz details",
    description="Get full quiz details with questions and answers (for owner/admin).",
)
async def get_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> QuizDetailResponse:
    """
    Get full quiz details with all questions and answers.

    **For owner/admin use** - includes `is_correct` field in answers.

    **Returns:**
    - Quiz with all questions and answers (including correct answer indicators)
    """
    quiz = await quiz_service.get_quiz(quiz_id=quiz_id, current_user=current_user)
    return QuizDetailResponse.model_validate(quiz)


@router.get(
    "/{quiz_id}/take",
    response_model=QuizPublicDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get quiz for taking (public)",
    description="Get quiz for users to take - without correct answer indicators.",
)
async def get_quiz_for_taking(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> QuizPublicDetailResponse:
    """
    Get quiz for users to take.

    **Public version** - does NOT include `is_correct` field in answers.
    Users see questions and answer options, but not which answers are correct.

    **Returns:**
    - Quiz with questions and answer options (without correct answer indicators)
    """
    quiz = await quiz_service.get_quiz_for_user(quiz_id=quiz_id)
    return QuizPublicDetailResponse.model_validate(quiz)


@router.put(
    "/{quiz_id}",
    response_model=QuizDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Update quiz",
    description="Update quiz title, description, or questions. Only company owner/admin can update.",
)
async def update_quiz(
    quiz_id: int,
    data: QuizUpdateRequest,
    current_user: User = Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> QuizDetailResponse:
    """
    Update an existing quiz.

    **Requirements:**
    - User must be owner or admin of the company
    - If updating questions: must have at least 2 questions
    - Each question must have 2-4 answers
    - Each question must have at least 1 correct answer

    **Note:**
    - If `questions` field is provided, ALL old questions will be deleted and replaced
    - If you want to keep existing questions, don't include `questions` field

    **Returns:**
    - Updated quiz with all questions and answers
    """
    quiz = await quiz_service.update_quiz(
        quiz_id=quiz_id,
        current_user=current_user,
        data=data,
    )

    return QuizDetailResponse.model_validate(quiz)


@router.delete(
    "/{quiz_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete quiz",
    description="Delete quiz with all questions and answers. Only company owner/admin can delete.",
)
async def delete_quiz(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    quiz_service: QuizService = Depends(get_quiz_service),
) -> None:
    """
    Delete a quiz.

    **Requirements:**
    - User must be owner or admin of the company

    **Note:**
    - This will CASCADE delete all questions and answers
    - This action cannot be undone

    **Returns:**
    - 204 No Content on success
    """
    await quiz_service.delete_quiz(
        quiz_id=quiz_id,
        current_user=current_user,
    )
