from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.pagination.pagination import PaginatedResponseBaseSchema


class AverageScoreResponse(BaseModel):
    """
    Average score entity for analytics (0..1).

    Used for:
    - company users average scores within date range
    - company user quiz average scores within date range
    """

    average_score: float = Field(..., ge=0.0, le=1.0)

    # Optional identifiers depending on aggregation level
    user_id: int | None = None
    quiz_id: int | None = None
    quiz_title: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CompanyUsersAveragesListResponse(
    PaginatedResponseBaseSchema[AverageScoreResponse]
):
    """
    Paginated average scores for all users in a company within date range.
    """

    pass


class CompanyUserQuizAveragesListResponse(
    PaginatedResponseBaseSchema[AverageScoreResponse]
):
    """
    Paginated average scores per quiz for a selected user in a company within date range.
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
