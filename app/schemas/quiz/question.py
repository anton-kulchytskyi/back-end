from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.quiz.answer import (
    QuizAnswerCreateRequest,
    QuizAnswerPublicResponse,
    QuizAnswerResponse,
)

T = TypeVar("T")


class QuizQuestionCreateRequest(BaseModel):
    """Schema for creating a quiz question."""

    title: str = Field(..., min_length=1, max_length=1000)
    answers: list[QuizAnswerCreateRequest] = Field(..., min_length=2, max_length=4)

    @model_validator(mode="after")
    def validate_answers(self):
        correct_count = sum(1 for a in self.answers if a.is_correct)
        if correct_count < 1:
            raise ValueError("Question must have at least 1 correct answer")
        return self

    model_config = {"from_attributes": True}


class QuizQuestionResponseBase(BaseModel, Generic[T]):
    id: int
    title: str
    answers: list[T]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuizQuestionPublicResponse(QuizQuestionResponseBase[QuizAnswerPublicResponse]):
    pass


class QuizQuestionResponse(QuizQuestionResponseBase[QuizAnswerResponse]):
    pass
