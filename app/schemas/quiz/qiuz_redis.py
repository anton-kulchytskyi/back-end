from datetime import datetime

from pydantic import BaseModel


class RedisQuizAnswerData(BaseModel):
    user_id: int
    company_id: int
    quiz_id: int
    question_id: int
    answer_id: int
    is_correct: bool
    attempt_id: int | None = None
    answered_at: datetime
