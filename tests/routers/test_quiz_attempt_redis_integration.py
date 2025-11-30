import pytest
from fakeredis.aioredis import FakeRedis
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_quiz_attempt_stores_answers_in_redis(
    client: AsyncClient,
    test_user,
    test_user_token: str,
    override_dependencies_fixture,
    test_quiz,
):
    fake_redis: FakeRedis = override_dependencies_fixture
    quiz_id = test_quiz.id

    payload = {
        "answers": [
            {
                "question_id": test_quiz.questions[0].id,
                "answer_id": test_quiz.questions[0].answers[0].id,
            },
            {
                "question_id": test_quiz.questions[1].id,
                "answer_id": test_quiz.questions[1].answers[0].id,
            },
        ]
    }

    response = await client.post(
        f"/quiz-attempts/quizzes/{quiz_id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 201, response.text

    keys = await fake_redis.keys("quiz-answer:*")
    assert len(keys) == 2, f"Expected 2 keys in Redis, but got {keys}"

    data = await fake_redis.hgetall(keys[0])

    assert data["user_id"] == str(test_user.id)
    assert data["quiz_id"] == str(quiz_id)
    assert data["company_id"] == str(test_quiz.company_id)
    assert "answered_at" in data
    assert data["attempt_id"].isdigit()

    assert data["is_correct"] in ("0", "1")
