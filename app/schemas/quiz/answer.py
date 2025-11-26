from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QuizAnswerCreateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    is_correct: bool


class QuizAnswerPublicResponse(BaseModel):
    """Without is_correct - for users taking quiz."""

    id: int
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuizAnswerResponse(QuizAnswerPublicResponse):
    is_correct: bool
