from __future__ import annotations

from datetime import timedelta
from typing import Any

from redis.asyncio import Redis

from app.schemas.quiz.qiuz_redis import RedisQuizAnswerData


class RedisQuizService:
    """Temporary storage of quiz answers in Redis for 48 hours."""

    TTL_SECONDS = int(timedelta(hours=48).total_seconds())

    def __init__(self, redis: Redis):
        self._redis = redis

    @staticmethod
    def _build_key(
        user_id: int,
        quiz_id: int,
        question_id: int,
        attempt_id: int,
    ) -> str:
        return f"quiz-answer:{user_id}:{quiz_id}:{question_id}:{attempt_id}"

    async def save_answer(self, data: RedisQuizAnswerData) -> None:
        key = self._build_key(
            user_id=data.user_id,
            quiz_id=data.quiz_id,
            question_id=data.question_id,
            attempt_id=data.attempt_id,
        )

        mapping: dict[str, Any] = {
            "user_id": str(data.user_id),
            "company_id": str(data.company_id),
            "quiz_id": str(data.quiz_id),
            "question_id": str(data.question_id),
            "answer_id": str(data.answer_id),
            "is_correct": "1" if data.is_correct else "0",
            "attempt_id": str(data.attempt_id),
            "answered_at": data.answered_at.isoformat(),
        }

        await self._redis.hset(key, mapping=mapping)
        await self._redis.expire(key, self.TTL_SECONDS)
