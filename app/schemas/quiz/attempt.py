from datetime import datetime

from pydantic import BaseModel, ConfigDict


class QuizAttemptCreateRequest(BaseModel):
    """Start quiz attempt."""

    quiz_id: int


class QuizAttemptResponse(BaseModel):
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

    model_config = ConfigDict(from_attributes=True)
