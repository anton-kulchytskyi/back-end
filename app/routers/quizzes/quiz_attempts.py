from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, get_quiz_attempt_service
from app.models import User
from app.schemas.pagination.pagination import PaginationBaseSchema
from app.schemas.quiz.attempt import (
    QuizAttemptResponse,
    QuizAttemptsListResponse,
    QuizAttemptSubmitRequest,
    UserQuizStatisticsResponse,
)
from app.services.quiz.quiz_attempt_service import QuizAttemptService

router = APIRouter()


@router.post(
    "/quizzes/{quiz_id}/attempt",
    response_model=QuizAttemptResponse,
    status_code=201,
    summary="Submit quiz attempt",
    description=(
        "Submit answers for a quiz. User must be authenticated and company must be visible. "
        "All questions must be answered exactly once."
    ),
)
async def submit_quiz_attempt(
    quiz_id: int,
    data: QuizAttemptSubmitRequest,
    current_user: User = Depends(get_current_user),
    service: QuizAttemptService = Depends(get_quiz_attempt_service),
) -> QuizAttemptResponse:
    """
    Submit a quiz attempt with answers.

    **Requirements:**
    - User must be authenticated
    - Company must be visible (is_visible=True)
    - Must answer all questions exactly once
    - No duplicate answers for the same question

    **Returns:**
    - Quiz attempt with score and results
    """
    return await service.submit_quiz_attempt(
        quiz_id=quiz_id,
        current_user=current_user,
        data=data,
    )


@router.get(
    "/users/me/statistics",
    response_model=UserQuizStatisticsResponse,
    summary="Get user quiz statistics",
    description=(
        "Get authenticated user's quiz statistics. "
        "Optionally filter by company to get company-specific average."
    ),
)
async def get_user_statistics(
    current_user: User = Depends(get_current_user),
    service: QuizAttemptService = Depends(get_quiz_attempt_service),
    company_id: int | None = Query(None, description="Filter by company ID"),
) -> UserQuizStatisticsResponse:
    """
    Get user's quiz statistics.

    **Returns:**
    - `global_average`: Average score across all quizzes (percentage)
    - `company_average`: Average for specific company if filtered (percentage)
    - `total_quizzes_taken`: Total number of completed quizzes
    - `last_attempt_at`: Timestamp of last completed attempt

    **Note:** Averages are calculated as: (total correct answers / total questions) * 100
    """
    return await service.get_user_statistics(
        current_user=current_user,
        company_id=company_id,
    )


@router.get(
    "/users/me/history",
    response_model=QuizAttemptsListResponse,
    summary="Get user quiz history",
    description=(
        "Get paginated list of authenticated user's quiz attempts. "
        "Can be filtered by company and/or quiz."
    ),
)
async def get_user_quiz_history(
    pagination: PaginationBaseSchema = Depends(),
    current_user: User = Depends(get_current_user),
    service: QuizAttemptService = Depends(get_quiz_attempt_service),
    company_id: int | None = Query(None, description="Filter by company ID"),
    quiz_id: int | None = Query(None, description="Filter by quiz ID"),
) -> QuizAttemptsListResponse:
    """
    Get paginated history of user's quiz attempts.

    **Query Parameters:**
    - `company_id`: Optional filter by company
    - `quiz_id`: Optional filter by quiz

    **Returns:**
    - Paginated list of quiz attempts with results
    - Sorted by completion date (newest first)
    """

    return await service.get_user_quiz_history(
        current_user=current_user,
        pagination=pagination,
        company_id=company_id,
        quiz_id=quiz_id,
    )
