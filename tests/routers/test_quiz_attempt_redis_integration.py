from fakeredis.aioredis import FakeRedis
from httpx import AsyncClient


async def test_quiz_attempt_stores_answers_in_redis(
    client: AsyncClient,
    test_user,
    test_user_token: str,
    override_dependencies_fixture,
    test_quiz,
):
    """Test that submitting quiz attempt stores answers in Redis."""
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

    assert (
        response.status_code == 201
    ), f"Failed with: {response.status_code} - {response.text}"

    # Verify Redis storage
    keys = await fake_redis.keys("quiz-answer:*")
    assert len(keys) == 2, f"Expected 2 keys in Redis, but got {len(keys)}: {keys}"

    data = await fake_redis.hgetall(keys[0])

    assert data["user_id"] == str(test_user.id)
    assert data["quiz_id"] == str(quiz_id)
    assert data["company_id"] == str(test_quiz.company_id)
    assert "answered_at" in data
    assert data["attempt_id"].isdigit()
    assert data["is_correct"] in ("0", "1")


async def test_quiz_attempt_correct_answer_flags(
    client: AsyncClient,
    test_user,
    test_user_token: str,
    test_quiz,
    override_dependencies_fixture,
):
    """Test that is_correct flag is properly set for correct/wrong answers."""
    fake_redis: FakeRedis = override_dependencies_fixture
    quiz_id = test_quiz.id

    # Get correct and wrong answer IDs
    q1_correct_answer = next(a for a in test_quiz.questions[0].answers if a.is_correct)
    q2_wrong_answer = next(
        a for a in test_quiz.questions[1].answers if not a.is_correct
    )

    payload = {
        "answers": [
            {
                "question_id": test_quiz.questions[0].id,
                "answer_id": q1_correct_answer.id,  # Correct answer
            },
            {
                "question_id": test_quiz.questions[1].id,
                "answer_id": q2_wrong_answer.id,  # Wrong answer
            },
        ]
    }

    response = await client.post(
        f"/quiz-attempts/quizzes/{quiz_id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert (
        response.status_code == 201
    ), f"Failed with: {response.status_code} - {response.text}"

    # Get all Redis keys
    keys = await fake_redis.keys("quiz-answer:*")
    assert len(keys) == 2, f"Expected 2 keys but got {len(keys)}"

    # Find the answers by question_id
    correct_count = 0
    wrong_count = 0

    for key in keys:
        data = await fake_redis.hgetall(key)
        if data["question_id"] == str(test_quiz.questions[0].id):
            # Should be correct
            assert data["is_correct"] == "1"
            correct_count += 1
        elif data["question_id"] == str(test_quiz.questions[1].id):
            # Should be wrong
            assert data["is_correct"] == "0"
            wrong_count += 1

    assert correct_count == 1
    assert wrong_count == 1


async def test_quiz_attempt_stores_all_required_fields(
    client: AsyncClient,
    test_user,
    test_user_token: str,
    test_quiz,
    override_dependencies_fixture,
):
    """Test that all required fields are stored in Redis."""
    fake_redis: FakeRedis = override_dependencies_fixture
    quiz_id = test_quiz.id

    # Submit with ALL questions (not just 1!)
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

    assert (
        response.status_code == 201
    ), f"Failed with: {response.status_code} - {response.text}"

    # Get Redis data
    keys = await fake_redis.keys("quiz-answer:*")
    assert len(keys) == 2, f"Expected 2 keys but got {len(keys)}"

    # Check first answer
    data = await fake_redis.hgetall(keys[0])

    # Assert all required fields from BE #13
    required_fields = [
        "user_id",
        "company_id",
        "quiz_id",
        "question_id",
        "answer_id",
        "is_correct",
        "attempt_id",
        "answered_at",
    ]

    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Assert field types
    assert data["user_id"].isdigit()
    assert data["company_id"].isdigit()
    assert data["quiz_id"].isdigit()
    assert data["question_id"].isdigit()
    assert data["answer_id"].isdigit()
    assert data["is_correct"] in ("0", "1")
    assert data["attempt_id"].isdigit()
    # ISO format timestamp
    assert "T" in data["answered_at"]


async def test_multiple_attempts_create_separate_redis_keys(
    client: AsyncClient,
    test_user,
    test_user_token: str,
    test_quiz,
    override_dependencies_fixture,
):
    """Test that multiple attempts create separate Redis keys."""
    fake_redis: FakeRedis = override_dependencies_fixture
    quiz_id = test_quiz.id

    # Submit with ALL questions
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

    # Act - submit first attempt
    response1 = await client.post(
        f"/quiz-attempts/quizzes/{quiz_id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert (
        response1.status_code == 201
    ), f"Attempt 1 failed: {response1.status_code} - {response1.text}"
    attempt1_id = response1.json()["id"]

    # Act - submit second attempt
    response2 = await client.post(
        f"/quiz-attempts/quizzes/{quiz_id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert (
        response2.status_code == 201
    ), f"Attempt 2 failed: {response2.status_code} - {response2.text}"
    attempt2_id = response2.json()["id"]

    # Assert - different attempt IDs
    assert attempt1_id != attempt2_id

    # Assert - 4 keys in Redis (2 answers per attempt × 2 attempts)
    keys = await fake_redis.keys("quiz-answer:*")
    assert (
        len(keys) == 4
    ), f"Expected 4 keys (2 attempts × 2 questions) but got {len(keys)}"

    # Assert - different attempt_ids in Redis
    attempt_ids_in_redis = set()
    for key in keys:
        data = await fake_redis.hgetall(key)
        attempt_ids_in_redis.add(data["attempt_id"])

    assert len(attempt_ids_in_redis) == 2, "Should have 2 different attempt IDs"
    assert attempt_ids_in_redis == {str(attempt1_id), str(attempt2_id)}
