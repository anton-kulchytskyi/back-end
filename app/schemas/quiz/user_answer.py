from datetime import datetime

from pydantic import BaseModel, ConfigDict


class QuizUserAnswerCreateRequest(BaseModel):
    """Submit answer to question."""

    question_id: int
    answer_id: int


class QuizUserAnswerResponse(BaseModel):
    id: int
    question_id: int
    answer_id: int
    is_correct: bool
    answered_at: datetime

    model_config = ConfigDict(from_attributes=True)
