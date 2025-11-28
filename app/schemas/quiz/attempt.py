from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pagination.pagination import PaginatedResponseBaseSchema

# --- Request Schemas ---


class QuestionAnswerSubmitRequest(BaseModel):
    """Single answer submission."""

    question_id: int = Field(..., gt=0)
    answer_id: int = Field(..., gt=0)


class QuizAttemptSubmitRequest(BaseModel):
    """Submit all answers for quiz attempt."""

    answers: list[QuestionAnswerSubmitRequest] = Field(..., min_length=1)


# --- Response Schemas ---


class QuizBriefResponse(BaseModel):
    """Brief quiz info for attempt response."""

    id: int
    title: str

    model_config = ConfigDict(from_attributes=True)


class CompanyBriefResponse(BaseModel):
    """Brief company info for attempt response."""

    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class QuizAttemptResponse(BaseModel):
    """Full quiz attempt response with results."""

    id: int
    user_id: int
    quiz_id: int
    company_id: int
    score: int
    total_questions: int
    percentage_score: float
    started_at: datetime
    completed_at: datetime | None
    is_completed: bool

    # Nested relations
    quiz: QuizBriefResponse
    company: CompanyBriefResponse

    model_config = ConfigDict(from_attributes=True)


class UserQuizStatisticsResponse(BaseModel):
    """User's quiz statistics."""

    global_average: float | None = Field(
        None,
        description="Global average score across all quizzes (percentage)",
    )
    company_average: float | None = Field(
        None,
        description="Average score for specific company (percentage, if filtered)",
    )
    total_quizzes_taken: int = Field(
        0,
        description="Total number of completed quiz attempts",
    )
    last_attempt_at: datetime | None = Field(
        None,
        description="Timestamp of last completed attempt",
    )


class QuizAttemptsListResponse(PaginatedResponseBaseSchema[QuizAttemptResponse]):
    """Paginated list of quiz attempts using unified pagination."""

    pass
