from .company_analytics import (
    AverageScoreResponse,
    CompanyUserLastAttemptResponse,
    CompanyUserQuizAveragesListResponse,
    CompanyUsersAveragesListResponse,
    CompanyUsersLastAttemptsListResponse,
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
    "AverageScoreResponse",
    "CompanyUsersAveragesListResponse",
    "CompanyUserQuizAveragesListResponse",
    "CompanyUserLastAttemptResponse",
    "CompanyUsersLastAttemptsListResponse",
]
