from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pagination.pagination import PaginatedResponseBaseSchema


class UserOverallRatingResponse(BaseModel):
    """
    Overall user rating across all quizzes and companies.
    """

    average_score: float = Field(..., ge=0.0, le=1.0)
    total_answers: int = Field(..., ge=0)
    correct_answers: int = Field(..., ge=0)

    model_config = ConfigDict(from_attributes=True)


class UserQuizAverageResponse(BaseModel):
    """
    Average score for a specific quiz in a given time range.
    """

    quiz_id: int
    quiz_title: str
    average_score: float = Field(..., ge=0.0, le=1.0)

    model_config = ConfigDict(from_attributes=True)


class UserQuizAveragesListResponse(
    PaginatedResponseBaseSchema[UserQuizAverageResponse]
):
    """
    Paginated list of quiz average scores for a user.
    """

    pass


class UserQuizLastCompletionResponse(BaseModel):
    """
    Last completion timestamp for a quiz.
    """

    quiz_id: int
    quiz_title: str
    last_completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserQuizLastCompletionListResponse(
    PaginatedResponseBaseSchema[UserQuizLastCompletionResponse]
):
    """
    Paginated list of quizzes with last completion timestamps.
    """

    pass
