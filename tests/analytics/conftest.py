from datetime import datetime, timedelta, timezone

import pytest_asyncio
from sqlalchemy import select

from app.models import QuizAttempt, QuizQuestion, QuizUserAnswer


async def create_quiz_attempt_with_answers(
    session,
    user_id: int,
    quiz_id: int,
    company_id: int,
    questions: list,
    correct_count: int,
    completed_at: datetime,
):
    """
    Helper to create a quiz attempt with specified number of correct answers.
    """
    total_questions = len(questions)

    attempt = QuizAttempt(
        user_id=user_id,
        quiz_id=quiz_id,
        company_id=company_id,
        total_questions=total_questions,
        completed_at=completed_at,
    )
    session.add(attempt)
    await session.flush()

    # Create answers
    for idx, question in enumerate(questions):
        is_correct = idx < correct_count

        if is_correct:
            selected_answer = next(a for a in question.answers if a.is_correct)
        else:
            selected_answer = next(a for a in question.answers if not a.is_correct)

        answer = QuizUserAnswer(
            user_id=user_id,
            attempt_id=attempt.id,
            question_id=question.id,
            answer_id=selected_answer.id,
            is_correct=is_correct,
            answered_at=completed_at,
        )
        session.add(answer)

    await session.commit()
    await session.refresh(attempt)
    return attempt


@pytest_asyncio.fixture
async def user_with_quiz_attempts(
    db_session, analytics_user_1, analytics_quiz, analytics_quiz_2, analytics_company
):
    # Get questions with answers for quiz 1
    result = await db_session.execute(
        select(QuizQuestion)
        .where(QuizQuestion.quiz_id == analytics_quiz.id)
        .order_by(QuizQuestion.id)
    )
    quiz_1_questions = result.scalars().all()

    for question in quiz_1_questions:
        await db_session.refresh(question, ["answers"])

    # Get questions with answers for quiz 2
    result = await db_session.execute(
        select(QuizQuestion)
        .where(QuizQuestion.quiz_id == analytics_quiz_2.id)
        .order_by(QuizQuestion.id)
    )
    quiz_2_questions = result.scalars().all()

    for question in quiz_2_questions:
        await db_session.refresh(question, ["answers"])

    now = datetime.now(timezone.utc)

    # Quiz 1 - Attempt 1: 4/5 correct (3 days ago)
    await create_quiz_attempt_with_answers(
        db_session,
        analytics_user_1.id,
        analytics_quiz.id,
        analytics_company.id,
        quiz_1_questions,
        correct_count=4,
        completed_at=now - timedelta(days=3),
    )

    # Quiz 1 - Attempt 2: 3/5 correct (1 day ago)
    await create_quiz_attempt_with_answers(
        db_session,
        analytics_user_1.id,
        analytics_quiz.id,
        analytics_company.id,
        quiz_1_questions,
        correct_count=3,
        completed_at=now - timedelta(days=1),
    )

    # Quiz 2 - Attempt 1: 2/3 correct (2 days ago)
    await create_quiz_attempt_with_answers(
        db_session,
        analytics_user_1.id,
        analytics_quiz_2.id,
        analytics_company.id,
        quiz_2_questions,
        correct_count=2,
        completed_at=now - timedelta(days=2),
    )

    return analytics_user_1


@pytest_asyncio.fixture
async def multiple_users_with_attempts(
    db_session,
    analytics_user_1,
    analytics_user_2,
    analytics_quiz,
    analytics_company,
):
    """
    Create attempts for multiple users:
    - User 1: 2 attempts in different weeks
    - User 2: 1 attempt
    """
    result = await db_session.execute(
        select(QuizQuestion)
        .where(QuizQuestion.quiz_id == analytics_quiz.id)
        .order_by(QuizQuestion.id)
    )
    questions = result.scalars().all()

    for question in questions:
        await db_session.refresh(question, ["answers"])

    now = datetime.now(timezone.utc)

    # User 1 - Week 1: 5/5 correct
    await create_quiz_attempt_with_answers(
        db_session,
        analytics_user_1.id,
        analytics_quiz.id,
        analytics_company.id,
        questions,
        correct_count=5,
        completed_at=now - timedelta(days=14),  # 2 weeks ago
    )

    # User 1 - Week 2: 3/5 correct
    await create_quiz_attempt_with_answers(
        db_session,
        analytics_user_1.id,
        analytics_quiz.id,
        analytics_company.id,
        questions,
        correct_count=3,
        completed_at=now - timedelta(days=7),  # 1 week ago
    )

    # User 2 - Week 2: 4/5 correct
    await create_quiz_attempt_with_answers(
        db_session,
        analytics_user_2.id,
        analytics_quiz.id,
        analytics_company.id,
        questions,
        correct_count=4,
        completed_at=now - timedelta(days=5),  # 5 days ago
    )

    return (analytics_user_1, analytics_user_2)
