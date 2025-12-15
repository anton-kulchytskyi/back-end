from .company_analytics import (
    CompanyUserLastAttemptResponse,
    CompanyUserQuizWeeklyAveragesListResponse,
    CompanyUsersLastAttemptsListResponse,
    CompanyUsersWeeklyAveragesListResponse,
    WeeklyAverageResponse,
)
from .user_analytics import (
    UserOverallRatingResponse,
    UserQuizAverageResponse,
    UserQuizAveragesListResponse,
    UserQuizLastCompletionListResponse,
    UserQuizLastCompletionResponse,
)

__all__ = [
    # User analytics
    "UserOverallRatingResponse",
    "UserQuizAverageResponse",
    "UserQuizAveragesListResponse",
    "UserQuizLastCompletionResponse",
    "UserQuizLastCompletionListResponse",
    # Company analytics
    "WeeklyAverageResponse",
    "CompanyUsersWeeklyAveragesListResponse",
    "CompanyUserQuizWeeklyAveragesListResponse",
    "CompanyUserLastAttemptResponse",
    "CompanyUsersLastAttemptsListResponse",
]
