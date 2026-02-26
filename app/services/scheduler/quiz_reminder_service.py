"""Quiz reminder service — sends notifications to users who missed daily quizzes."""

from datetime import datetime, timedelta, timezone
from typing import Callable

from app.core.logger import logger
from app.core.unit_of_work import AbstractUnitOfWork, SQLAlchemyUnitOfWork
from app.enums.notification_status import NotificationStatus
from app.models.notification.notification import Notification


class QuizReminderService:
    """
    Checks all quizzes daily and notifies company members
    who have not completed a quiz in the last 24 hours.
    """

    REMINDER_WINDOW_HOURS = 24

    def __init__(self, uow_factory: Callable[[], AbstractUnitOfWork] | None = None):
        self._uow_factory = uow_factory or SQLAlchemyUnitOfWork

    async def send_quiz_reminders(self) -> int:
        """
        Main entry point called by the scheduler.

        Returns:
            Total number of notifications created.
        """
        since = datetime.now(timezone.utc) - timedelta(hours=self.REMINDER_WINDOW_HOURS)
        total = 0

        async with self._uow_factory() as uow:
            quizzes, _ = await uow.quiz.get_all(skip=0, limit=100_000)

            for quiz in quizzes:
                user_ids = await uow.quiz_attempt.get_users_without_recent_attempt(
                    quiz_id=quiz.id,
                    company_id=quiz.company_id,
                    since=since,
                )

                for user_id in user_ids:
                    notification = Notification(
                        user_id=user_id,
                        message=(
                            f'Don\'t forget to complete quiz "{quiz.title}" '
                            f"— you haven't done it today!"
                        ),
                        status=NotificationStatus.UNREAD,
                    )
                    await uow.notifications.create_one(notification)
                    total += 1

            if total > 0:
                await uow.commit()

        logger.info("Quiz reminders sent: %s notifications created", total)
        return total
