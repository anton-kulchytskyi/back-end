from datetime import datetime, timedelta

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.exceptions import RedisException
from app.core.logger import logger
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

    @staticmethod
    def _decode_redis_data(raw_data: dict) -> dict[str, str]:
        """
        Decode bytes from Redis to strings.
        Supports both bytes and str (for fakeredis / decode_responses=True).
        """
        return {
            (k.decode("utf-8") if isinstance(k, bytes) else k): (
                v.decode("utf-8") if isinstance(v, bytes) else v
            )
            for k, v in raw_data.items()
        }

    @staticmethod
    def _parse_redis_data(data: dict[str, str]) -> RedisQuizAnswerData:
        """
        Parse Redis string data into RedisQuizAnswerData model.
        """
        return RedisQuizAnswerData(
            user_id=int(data["user_id"]),
            company_id=int(data["company_id"]),
            quiz_id=int(data["quiz_id"]),
            question_id=int(data["question_id"]),
            answer_id=int(data["answer_id"]),
            is_correct=data["is_correct"] == "1",
            attempt_id=int(data["attempt_id"]),
            answered_at=datetime.fromisoformat(data["answered_at"]),
        )

    async def save_answers_bulk(self, answers: list[RedisQuizAnswerData]) -> None:
        """Save multiple answers atomically using a pipeline."""

        if not answers:
            logger.debug("No answers to save to Redis")
            return

        try:
            async with self._redis.pipeline(transaction=True) as pipe:
                for data in answers:
                    key = self._build_key(
                        user_id=data.user_id,
                        quiz_id=data.quiz_id,
                        question_id=data.question_id,
                        attempt_id=data.attempt_id,
                    )

                    mapping = {
                        "user_id": str(data.user_id),
                        "company_id": str(data.company_id),
                        "quiz_id": str(data.quiz_id),
                        "question_id": str(data.question_id),
                        "answer_id": str(data.answer_id),
                        "is_correct": "1" if data.is_correct else "0",
                        "attempt_id": str(data.attempt_id),
                        "answered_at": data.answered_at.isoformat(),
                    }

                    await pipe.hset(key, mapping=mapping)
                    await pipe.expire(key, self.TTL_SECONDS)

                await pipe.execute()

            logger.info(
                "Saved %s answers to Redis",
                len(answers),
                extra={"answer_count": len(answers)},
            )

        except RedisError as e:
            logger.error(
                "Failed to bulk save %s answers to Redis: %s",
                len(answers),
                e,
                extra={"answer_count": len(answers)},
                exc_info=True,
            )
            raise RedisException(
                f"Failed to bulk save {len(answers)} answers to Redis: {e}"
            )

    async def fetch_answers(
        self,
        user_id: int | None = None,
        company_id: int | None = None,
        quiz_id: int | None = None,
    ) -> list[RedisQuizAnswerData]:
        """Fetch answers from Redis with flexible filters."""
        # Build key pattern:
        # quiz-answer:{user_id or *}:{quiz_id or *}:*:*.
        user_segment = str(user_id) if user_id is not None else "*"
        quiz_segment = str(quiz_id) if quiz_id is not None else "*"
        pattern = f"quiz-answer:{user_segment}:{quiz_segment}:*:*"

        answers: list[RedisQuizAnswerData] = []

        try:
            async for key in self._redis.scan_iter(match=pattern, count=100):
                raw_data = await self._redis.hgetall(key)
                if not raw_data:
                    continue

                decoded = self._decode_redis_data(raw_data)
                parsed = self._parse_redis_data(decoded)

                if company_id is not None and parsed.company_id != company_id:
                    continue

                answers.append(parsed)

            logger.info(
                "Fetched %s answers from Redis",
                len(answers),
                extra={
                    "user_id": user_id,
                    "company_id": company_id,
                    "quiz_id": quiz_id,
                    "count": len(answers),
                },
            )

            return answers

        except RedisError as e:
            logger.error(
                "Failed to fetch answers from Redis: %s",
                e,
                extra={
                    "user_id": user_id,
                    "company_id": company_id,
                    "quiz_id": quiz_id,
                },
                exc_info=True,
            )
            raise RedisException(f"Failed to fetch answers from Redis: {e}")

    async def get_user_answers(
        self,
        user_id: int,
        quiz_id: int | None = None,
    ) -> list[RedisQuizAnswerData]:
        """Get all answers for a user (optionally filtered by quiz)."""

        return await self.fetch_answers(user_id=user_id, quiz_id=quiz_id)

    async def get_company_answers(
        self,
        company_id: int,
        user_id: int | None = None,
        quiz_id: int | None = None,
    ) -> list[RedisQuizAnswerData]:
        """Get all answers for a company (optionally filtered by user and/or quiz)."""

        return await self.fetch_answers(
            user_id=user_id,
            company_id=company_id,
            quiz_id=quiz_id,
        )
