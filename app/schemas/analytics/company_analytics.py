from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pagination.pagination import PaginatedResponseBaseSchema


class WeeklyAverageResponse(BaseModel):
    """
    Weekly average score entity.
    Used for:
    - users weekly averages
    - quizzes weekly averages for a user
    """

    week_start: date
    average_score: float = Field(..., ge=0.0, le=1.0)

    # Optional identifiers depending on aggregation level
    user_id: int | None = None
    quiz_id: int | None = None
    quiz_title: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CompanyUsersWeeklyAveragesListResponse(
    PaginatedResponseBaseSchema[WeeklyAverageResponse]
):
    """
    Paginated weekly averages for all users in a company.
    """

    pass


class CompanyUserQuizWeeklyAveragesListResponse(
    PaginatedResponseBaseSchema[WeeklyAverageResponse]
):
    """
    Paginated weekly quiz averages for a selected user.
    """

    pass


class CompanyUserLastAttemptResponse(BaseModel):
    """
    Last quiz attempt timestamp for a user in a company.
    """

    user_id: int
    user_email: str
    last_attempt_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class CompanyUsersLastAttemptsListResponse(
    PaginatedResponseBaseSchema[CompanyUserLastAttemptResponse]
):
    """
    Paginated list of users with their last quiz attempt timestamps.
    """

    pass
