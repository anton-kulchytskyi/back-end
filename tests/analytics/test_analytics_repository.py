from datetime import date, datetime, timedelta, timezone

import pytest

from app.db.analytics.company_analytics_repository import CompanyAnalyticsRepository
from app.db.analytics.user_analytics_repository import UserAnalyticsRepository
from app.models import QuizAttempt, QuizUserAnswer


@pytest.mark.asyncio
async def test_user_overall_rating_empty(db_session, test_user):
    repo = UserAnalyticsRepository(db_session)

    correct, total = await repo.get_user_overall_rating(user_id=test_user.id)

    assert correct == 0
    assert total == 0


@pytest.mark.asyncio
async def test_user_overall_rating_with_answers(db_session, test_user, test_quiz):
    repo = UserAnalyticsRepository(db_session)

    attempt = QuizAttempt(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        company_id=test_quiz.company_id,
        total_questions=2,
    )
    db_session.add(attempt)
    await db_session.flush()

    db_session.add_all(
        [
            QuizUserAnswer(
                attempt_id=attempt.id,
                question_id=1,
                answer_id=1,
                is_correct=True,
            ),
            QuizUserAnswer(
                attempt_id=attempt.id,
                question_id=2,
                answer_id=2,
                is_correct=False,
            ),
        ]
    )
    await db_session.commit()

    correct, total = await repo.get_user_overall_rating(user_id=test_user.id)

    assert correct == 1
    assert total == 2


@pytest.mark.asyncio
async def test_user_quiz_averages_paginated(db_session, test_user, test_quiz):
    repo = UserAnalyticsRepository(db_session)

    attempt = QuizAttempt(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        company_id=test_quiz.company_id,
        total_questions=2,
    )
    db_session.add(attempt)
    await db_session.flush()

    db_session.add_all(
        [
            QuizUserAnswer(
                attempt_id=attempt.id,
                question_id=1,
                answer_id=1,
                is_correct=True,
            ),
            QuizUserAnswer(
                attempt_id=attempt.id,
                question_id=2,
                answer_id=2,
                is_correct=True,
            ),
        ]
    )
    await db_session.commit()

    items, total = await repo.get_user_quiz_averages_paginated(
        user_id=test_user.id,
        from_date=date(2000, 1, 1),
        to_date=date(2100, 1, 1),
        skip=0,
        limit=10,
    )

    assert total == 1
    assert len(items) == 1
    assert items[0].quiz_id == test_quiz.id
    assert items[0].average_score == 1.0


@pytest.mark.asyncio
async def test_user_last_completions_paginated(db_session, test_user, test_quiz):
    """Test getting last completion timestamps"""
    repo = UserAnalyticsRepository(db_session)

    completed_at = datetime.now(timezone.utc) - timedelta(hours=5)

    attempt = QuizAttempt(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        company_id=test_quiz.company_id,
        total_questions=2,
        completed_at=completed_at,
    )
    db_session.add(attempt)
    await db_session.commit()

    items, total = await repo.get_user_last_quiz_completions_paginated(
        user_id=test_user.id,
        skip=0,
        limit=10,
    )

    assert total == 1
    assert len(items) == 1
    assert items[0].quiz_id == test_quiz.id
    assert items[0].last_completed_at is not None


@pytest.mark.asyncio
async def test_company_user_quiz_averages_by_date_range(
    db_session,
    test_user,
    test_quiz,
):
    """Test average quiz score for a user in company within date range"""
    repo = CompanyAnalyticsRepository(db_session)

    now = datetime.now(timezone.utc)

    # Attempt 1 (inside range)
    attempt1 = QuizAttempt(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        company_id=test_quiz.company_id,
        total_questions=2,
        completed_at=now - timedelta(days=10),
    )
    db_session.add(attempt1)
    await db_session.flush()

    db_session.add_all(
        [
            QuizUserAnswer(
                attempt_id=attempt1.id,
                question_id=1,
                answer_id=1,
                is_correct=True,
            ),
            QuizUserAnswer(
                attempt_id=attempt1.id,
                question_id=2,
                answer_id=2,
                is_correct=True,
            ),
        ]
    )

    # Attempt 2 (inside range)
    attempt2 = QuizAttempt(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        company_id=test_quiz.company_id,
        total_questions=2,
        completed_at=now - timedelta(days=2),
    )
    db_session.add(attempt2)
    await db_session.flush()

    db_session.add_all(
        [
            QuizUserAnswer(
                attempt_id=attempt2.id,
                question_id=1,
                answer_id=1,
                is_correct=False,
            ),
            QuizUserAnswer(
                attempt_id=attempt2.id,
                question_id=2,
                answer_id=2,
                is_correct=True,
            ),
        ]
    )

    await db_session.commit()

    from_date = (now - timedelta(days=30)).date()
    to_date = now.date()

    items, total = await repo.get_company_user_quiz_averages_paginated(
        company_id=test_quiz.company_id,
        target_user_id=test_user.id,
        from_date=from_date,
        to_date=to_date,
        skip=0,
        limit=10,
    )

    assert total == 1
    assert len(items) == 1

    item = items[0]
    assert item.quiz_id == test_quiz.id
    assert item.quiz_title == test_quiz.title
    assert item.average_score == pytest.approx(0.75)
