from datetime import datetime, timezone

import pytest
from fakeredis.aioredis import FakeRedis

from app.schemas import RedisQuizAnswerData
from app.services.quiz.quiz_redis_service import RedisQuizService


@pytest.mark.asyncio
async def test_redis_quiz_service_save_answer():
    redis = FakeRedis(decode_responses=True)
    service = RedisQuizService(redis)

    payload = RedisQuizAnswerData(
        user_id=1,
        company_id=2,
        quiz_id=3,
        question_id=4,
        answer_id=5,
        is_correct=True,
        attempt_id=10,
        answered_at=datetime.now(timezone.utc),
    )

    await service.save_answer(payload)

    # перевіряємо ключ
    key = "quiz-answer:1:3:4:10"
    exists = await redis.exists(key)
    assert exists == 1

    stored = await redis.hgetall(key)
    assert stored["user_id"] == "1"
    assert stored["company_id"] == "2"
    assert stored["quiz_id"] == "3"
    assert stored["question_id"] == "4"
    assert stored["answer_id"] == "5"
    assert stored["is_correct"] == "1"
    assert stored["attempt_id"] == "10"

    ttl = await redis.ttl(key)
    assert ttl > 0
    assert ttl <= RedisQuizService.TTL_SECONDS
