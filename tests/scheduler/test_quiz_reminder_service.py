"""Tests for QuizReminderService."""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import Role
from app.enums.notification_status import NotificationStatus
from app.models import Company, CompanyMember, User
from app.models.quiz.quiz import Quiz
from app.models.quiz.quiz_attempt import QuizAttempt
from app.services.scheduler.quiz_reminder_service import QuizReminderService
from tests.conftest import TestSQLAlchemyUnitOfWork

# ==================== FIXTURES ====================


@pytest_asyncio.fixture
async def reminder_service(db_session: AsyncSession) -> QuizReminderService:
    def uow_factory():
        return TestSQLAlchemyUnitOfWork(db_session)

    return QuizReminderService(uow_factory=uow_factory)


@pytest_asyncio.fixture
async def company_with_quiz_and_members(db_session: AsyncSession):
    """
    Creates:
    - owner user
    - 2 member users
    - a company with all three as members
    - a quiz in that company
    """
    owner = User(email="owner@test.com", full_name="Owner", hashed_password="x")
    member1 = User(email="m1@test.com", full_name="Member 1", hashed_password="x")
    member2 = User(email="m2@test.com", full_name="Member 2", hashed_password="x")
    db_session.add_all([owner, member1, member2])
    await db_session.flush()

    company = Company(
        name="Reminder Co",
        description="desc",
        is_visible=True,
        owner_id=owner.id,
    )
    db_session.add(company)
    await db_session.flush()

    for user, role in [
        (owner, Role.OWNER),
        (member1, Role.MEMBER),
        (member2, Role.MEMBER),
    ]:
        db_session.add(CompanyMember(company_id=company.id, user_id=user.id, role=role))
    await db_session.flush()

    quiz = Quiz(title="Daily Quiz", description="desc", company_id=company.id)
    db_session.add(quiz)
    await db_session.flush()

    await db_session.commit()

    return {
        "company": company,
        "quiz": quiz,
        "owner": owner,
        "members": [member1, member2],
    }


# ==================== TESTS ====================


@pytest.mark.asyncio
async def test_sends_reminders_to_all_members_when_no_attempts(
    reminder_service: QuizReminderService,
    company_with_quiz_and_members: dict,
):
    """All company members with no attempts should receive a notification."""
    result = await reminder_service.send_quiz_reminders()

    # owner + 2 members = 3 notifications
    assert result == 3


@pytest.mark.asyncio
async def test_skips_user_with_recent_attempt(
    reminder_service: QuizReminderService,
    company_with_quiz_and_members: dict,
    db_session: AsyncSession,
):
    """User who completed the quiz recently should NOT receive a reminder."""
    data = company_with_quiz_and_members
    member1 = data["members"][0]
    quiz = data["quiz"]

    # member1 completed the quiz 1 hour ago
    attempt = QuizAttempt(
        user_id=member1.id,
        quiz_id=quiz.id,
        company_id=data["company"].id,
        total_questions=2,
        score=2,
        completed_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(attempt)
    await db_session.commit()

    result = await reminder_service.send_quiz_reminders()

    # owner + member2 = 2 notifications (member1 is skipped)
    assert result == 2


@pytest.mark.asyncio
async def test_sends_reminder_to_user_with_old_attempt(
    reminder_service: QuizReminderService,
    company_with_quiz_and_members: dict,
    db_session: AsyncSession,
):
    """User whose last attempt was more than 24h ago should receive a reminder."""
    data = company_with_quiz_and_members
    member1 = data["members"][0]
    quiz = data["quiz"]

    # member1 completed the quiz 25 hours ago (too old)
    attempt = QuizAttempt(
        user_id=member1.id,
        quiz_id=quiz.id,
        company_id=data["company"].id,
        total_questions=2,
        score=1,
        completed_at=datetime.now(timezone.utc) - timedelta(hours=25),
    )
    db_session.add(attempt)
    await db_session.commit()

    result = await reminder_service.send_quiz_reminders()

    # all 3 users need a reminder (old attempt counts as missing)
    assert result == 3


@pytest.mark.asyncio
async def test_no_notifications_when_no_quizzes(
    reminder_service: QuizReminderService,
):
    """If there are no quizzes at all, no notifications should be created."""
    result = await reminder_service.send_quiz_reminders()

    assert result == 0


@pytest.mark.asyncio
async def test_notification_message_contains_quiz_title(
    reminder_service: QuizReminderService,
    company_with_quiz_and_members: dict,
    db_session: AsyncSession,
):
    """Created notifications should contain the quiz title in the message."""
    quiz = company_with_quiz_and_members["quiz"]

    await reminder_service.send_quiz_reminders()

    from app.db.notification.notification_repository import NotificationRepository

    repo = NotificationRepository(db_session)
    notifications, _ = await repo.get_many_by_filters()

    assert all(quiz.title in n.message for n in notifications)
    assert all(n.status == NotificationStatus.UNREAD for n in notifications)
