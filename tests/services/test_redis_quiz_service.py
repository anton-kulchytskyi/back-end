from datetime import datetime, timezone

import pytest
import pytest_asyncio
from fakeredis.aioredis import FakeRedis

from app.schemas import RedisQuizAnswerData
from app.services.quiz.quiz_redis_service import RedisQuizService

# ============================================================================
# FIXTURES
# ============================================================================


@pytest_asyncio.fixture
async def fake_redis():
    """
    Create fresh FakeRedis instance for each test.

    This ensures test isolation - each test gets clean Redis state.
    """
    redis = FakeRedis(decode_responses=True)
    yield redis
    # Cleanup after test
    await redis.flushall()


@pytest_asyncio.fixture
def redis_quiz_service(fake_redis):
    """Create RedisQuizService with fresh FakeRedis."""
    return RedisQuizService(fake_redis)


# ============================================================================
# BULK SAVE TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_save_answers_bulk_empty_list(redis_quiz_service, fake_redis):
    """Test that save_answers_bulk handles empty list gracefully."""
    # Act
    await redis_quiz_service.save_answers_bulk([])

    # Assert - no keys should be created
    keys = await fake_redis.keys("quiz-answer:*")
    assert len(keys) == 0


@pytest.mark.asyncio
async def test_save_answers_bulk_multiple_answers(redis_quiz_service, fake_redis):
    """Test that save_answers_bulk saves multiple answers."""
    # Arrange
    answers = [
        RedisQuizAnswerData(
            user_id=123,
            company_id=456,
            quiz_id=789,
            question_id=i,
            answer_id=i + 10,
            is_correct=i % 2 == 0,  # Alternate True/False
            attempt_id=1,
            answered_at=datetime.now(timezone.utc),
        )
        for i in range(1, 4)  # 3 answers
    ]

    # Act
    await redis_quiz_service.save_answers_bulk(answers)

    # Assert - 3 keys should exist
    keys = await fake_redis.keys("quiz-answer:*")
    assert len(keys) == 3

    # Assert - check first answer
    key1 = "quiz-answer:123:789:1:1"
    stored1 = await fake_redis.hgetall(key1)
    assert stored1["question_id"] == "1"
    assert stored1["answer_id"] == "11"
    assert stored1["is_correct"] == "0"  # 1 % 2 == 1 (False)

    # Assert - check second answer
    key2 = "quiz-answer:123:789:2:1"
    stored2 = await fake_redis.hgetall(key2)
    assert stored2["question_id"] == "2"
    assert stored2["answer_id"] == "12"
    assert stored2["is_correct"] == "1"  # 2 % 2 == 0 (True)


@pytest.mark.asyncio
async def test_save_answers_bulk_sets_ttl_for_all(redis_quiz_service, fake_redis):
    """Test that save_answers_bulk sets TTL for all answers."""
    # Arrange
    answers = [
        RedisQuizAnswerData(
            user_id=123,
            company_id=456,
            quiz_id=789,
            question_id=i,
            answer_id=i + 10,
            is_correct=True,
            attempt_id=1,
            answered_at=datetime.now(timezone.utc),
        )
        for i in range(1, 4)
    ]

    # Act
    await redis_quiz_service.save_answers_bulk(answers)

    # Assert - all keys have TTL
    keys = await fake_redis.keys("quiz-answer:*")
    for key in keys:
        ttl = await fake_redis.ttl(key)
        assert ttl > 0
        assert ttl <= RedisQuizService.TTL_SECONDS


# ============================================================================
# KEY BUILDING TESTS
# ============================================================================


def test_build_key_correct_format():
    """Test Redis key building with correct format."""
    key = RedisQuizService._build_key(
        user_id=123,
        quiz_id=789,
        question_id=5,
        attempt_id=10,
    )

    assert key == "quiz-answer:123:789:5:10"


def test_build_key_with_different_ids():
    """Test Redis key building with various IDs."""
    key1 = RedisQuizService._build_key(1, 2, 3, 4)
    key2 = RedisQuizService._build_key(100, 200, 300, 400)

    assert key1 == "quiz-answer:1:2:3:4"
    assert key2 == "quiz-answer:100:200:300:400"


# ============================================================================
# TTL CONSTANT TESTS
# ============================================================================


def test_ttl_constant_is_48_hours():
    """Test that TTL constant is exactly 48 hours."""
    expected_seconds = 48 * 60 * 60  # 172800
    assert RedisQuizService.TTL_SECONDS == expected_seconds


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_bulk_save_different_attempts(redis_quiz_service, fake_redis):
    """Test bulk save with answers from different attempts."""
    # Arrange - 2 attempts, 2 questions each
    answers = []
    for attempt_id in [1, 2]:
        for question_id in [10, 20]:
            answers.append(
                RedisQuizAnswerData(
                    user_id=100,
                    company_id=200,
                    quiz_id=300,
                    question_id=question_id,
                    answer_id=question_id + 1,
                    is_correct=True,
                    attempt_id=attempt_id,
                    answered_at=datetime.now(timezone.utc),
                )
            )

    # Act
    await redis_quiz_service.save_answers_bulk(answers)

    # Assert - 4 keys total (2 attempts × 2 questions)
    keys = await fake_redis.keys("quiz-answer:*")
    assert len(keys) == 4, f"Expected 4 keys but got {len(keys)}: {keys}"

    # Assert - keys for attempt 1
    assert await fake_redis.exists("quiz-answer:100:300:10:1") == 1
    assert await fake_redis.exists("quiz-answer:100:300:20:1") == 1

    # Assert - keys for attempt 2
    assert await fake_redis.exists("quiz-answer:100:300:10:2") == 1
    assert await fake_redis.exists("quiz-answer:100:300:20:2") == 1
