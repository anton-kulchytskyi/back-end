from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.schemas import PaginatedResponseBaseSchema
from app.schemas.quiz.question import (
    QuizQuestionCreateRequest,
    QuizQuestionPublicResponse,
    QuizQuestionResponse,
)

T = TypeVar("T")


class QuizCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=5000)
    questions: list[QuizQuestionCreateRequest] = Field(..., min_length=2)


class QuizUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, min_length=1, max_length=5000)
    questions: list[QuizQuestionCreateRequest] | None = Field(None, min_length=2)


class QuizResponse(BaseModel):
    id: int
    title: str
    description: str
    company_id: int
    created_by: int | None
    total_questions_count: int
    participation_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuizResponseBase(QuizResponse, Generic[T]):
    questions: list[T]
    # model_config = ConfigDict(from_attributes=True)


class QuizDetailResponse(QuizResponseBase[QuizQuestionResponse]):
    """Full quiz with questions and correct answers."""

    pass


class QuizPublicDetailResponse(QuizResponseBase[QuizQuestionPublicResponse]):
    """Quiz for taking - without correct answers (for users)."""

    pass


class QuizzesListResponse(PaginatedResponseBaseSchema[QuizResponse]):
    pass
