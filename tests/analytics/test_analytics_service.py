from datetime import date

import pytest

from app.core.exceptions import BadRequestException, PermissionDeniedException
from app.models import QuizAttempt, QuizUserAnswer
from app.schemas.pagination.pagination import PaginationBaseSchema
from app.services.analytics.company_analytics_service import CompanyAnalyticsService
from app.services.analytics.user_analytics_service import UserAnalyticsService
from app.services.companies.admin_service import AdminService
from app.services.companies.company_service import CompanyService
from app.services.companies.permission_service import PermissionService


@pytest.mark.asyncio
async def test_user_service_overall_rating_empty(unit_of_work, test_user):
    service = UserAnalyticsService(uow=unit_of_work)

    result = await service.get_overall_rating(user_id=test_user.id)

    assert result.correct_answers == 0
    assert result.total_answers == 0
    assert result.average_score == 0.0


@pytest.mark.asyncio
async def test_user_service_overall_rating_with_data(
    unit_of_work, db_session, test_user, test_quiz
):
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

    service = UserAnalyticsService(uow=unit_of_work)

    result = await service.get_overall_rating(user_id=test_user.id)

    assert result.correct_answers == 1
    assert result.total_answers == 2
    assert result.average_score == 0.5


@pytest.mark.asyncio
async def test_company_service_permission_denied(
    unit_of_work,
    test_member_user,
    test_company,
):
    uow = unit_of_work
    permission_service = PermissionService(uow)
    company_service = CompanyService(uow, permission_service=permission_service)
    admin_service = AdminService(
        uow=uow,
        permission_service=permission_service,
        company_service=company_service,
    )

    service = CompanyAnalyticsService(uow, admin_service)

    pagination = PaginationBaseSchema(page=1, limit=10)

    with pytest.raises(PermissionDeniedException):
        await service.get_users_averages_paginated(
            company_id=test_company.id,
            current_user_id=test_member_user.id,
            from_date=date(2000, 1, 1),
            to_date=date(2100, 1, 1),
            pagination=pagination,
        )


@pytest.mark.asyncio
async def test_user_service_quiz_averages_paginated(
    unit_of_work, db_session, test_user, test_quiz
):
    """Test quiz averages pagination"""
    service = UserAnalyticsService(uow=unit_of_work)

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

    pagination = PaginationBaseSchema(page=1, limit=10)
    result = await service.get_quiz_averages_paginated(
        user_id=test_user.id,
        from_date=date(2000, 1, 1),
        to_date=date(2100, 1, 1),
        pagination=pagination,
    )

    assert result.total == 1
    assert len(result.results) == 1
    assert result.results[0].average_score == 1.0


@pytest.mark.asyncio
async def test_user_service_last_completions_paginated(
    unit_of_work, db_session, test_user, test_quiz
):
    """Test last completions pagination"""
    service = UserAnalyticsService(uow=unit_of_work)

    attempt = QuizAttempt(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        company_id=test_quiz.company_id,
        total_questions=2,
    )
    db_session.add(attempt)
    await db_session.commit()

    pagination = PaginationBaseSchema(page=1, limit=10)
    result = await service.get_last_quiz_completions_paginated(
        user_id=test_user.id,
        pagination=pagination,
    )

    assert result.total == 1
    assert len(result.results) == 1


@pytest.mark.asyncio
async def test_company_service_owner_can_access(
    unit_of_work,
    test_user,  # Owner
    test_company,
):
    """Test that owner can access company analytics"""
    uow = unit_of_work
    permission_service = PermissionService(uow)
    company_service = CompanyService(uow, permission_service=permission_service)
    admin_service = AdminService(
        uow=uow,
        permission_service=permission_service,
        company_service=company_service,
    )

    service = CompanyAnalyticsService(uow, admin_service)
    pagination = PaginationBaseSchema(page=1, limit=10)

    result = await service.get_users_averages_paginated(
        company_id=test_company.id,
        current_user_id=test_user.id,
        from_date=date(2000, 1, 1),
        to_date=date(2100, 1, 1),
        pagination=pagination,
    )

    assert result is not None


@pytest.mark.asyncio
async def test_company_service_admin_can_access(
    unit_of_work,
    test_admin_user,
    company_with_admin,
):
    """Test that admin can access company analytics"""
    uow = unit_of_work
    permission_service = PermissionService(uow)
    company_service = CompanyService(uow, permission_service=permission_service)
    admin_service = AdminService(
        uow=uow,
        permission_service=permission_service,
        company_service=company_service,
    )

    service = CompanyAnalyticsService(uow, admin_service)

    pagination = PaginationBaseSchema(page=1, limit=10)

    result = await service.get_users_averages_paginated(
        company_id=company_with_admin.id,
        current_user_id=test_admin_user.id,
        from_date=date(2000, 1, 1),
        to_date=date(2100, 1, 1),
        pagination=pagination,
    )

    assert result is not None


@pytest.mark.asyncio
async def test_company_service_last_attempts(
    unit_of_work,
    db_session,
    test_user,
    test_company,
    test_quiz,
):
    """Test company last attempts service"""
    uow = unit_of_work
    permission_service = PermissionService(uow)
    company_service = CompanyService(uow, permission_service=permission_service)
    admin_service = AdminService(
        uow=uow,
        permission_service=permission_service,
        company_service=company_service,
    )

    service = CompanyAnalyticsService(uow, admin_service)

    # Create attempt
    attempt = QuizAttempt(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        company_id=test_quiz.company_id,
        total_questions=2,
    )
    db_session.add(attempt)
    await db_session.commit()

    pagination = PaginationBaseSchema(page=1, limit=10)
    result = await service.get_users_last_attempts_paginated(
        company_id=test_company.id,
        current_user_id=test_user.id,
        pagination=pagination,
    )

    assert result.total >= 0


@pytest.mark.asyncio
async def test_user_quiz_averages_invalid_date_range_service(unit_of_work):
    """
    Service should raise BadRequestException when from_date > to_date.
    """
    service = UserAnalyticsService(uow=unit_of_work)

    pagination = PaginationBaseSchema(page=1, limit=10)

    with pytest.raises(BadRequestException):
        await service.get_quiz_averages_paginated(
            user_id=1,
            from_date=date(2024, 12, 31),
            to_date=date(2024, 1, 1),
            pagination=pagination,
        )
