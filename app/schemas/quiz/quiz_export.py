from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ExportFormat(str, Enum):
    """Export format enum."""

    JSON = "json"
    CSV = "csv"


class QuizAnswerExportData(BaseModel):
    """Single quiz answer for export."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": 123,
                "company_id": 456,
                "quiz_id": 789,
                "question_id": 1,
                "answer_id": 2,
                "is_correct": True,
                "attempt_id": 1,
                "answered_at": "2024-01-01T12:00:00+00:00",
            }
        },
    )

    user_id: int
    company_id: int
    quiz_id: int
    question_id: int
    answer_id: int
    is_correct: bool
    attempt_id: int
    answered_at: datetime


class ExportMetadata(BaseModel):
    """
    Metadata about the export.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_answers": 42,
                "user_id": 123,
                "company_id": None,
                "quiz_id": 456,
                "format": "json",
                "exported_at": "2024-01-01T12:00:00+00:00",
            }
        }
    )

    total_answers: int
    user_id: int | None = None
    company_id: int | None = None
    quiz_id: int | None = None
    format: ExportFormat
    exported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExportResponse(BaseModel):
    """
    Response model for JSON export.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": [
                    {
                        "user_id": 123,
                        "company_id": 456,
                        "quiz_id": 789,
                        "question_id": 1,
                        "answer_id": 2,
                        "is_correct": True,
                        "attempt_id": 1,
                        "answered_at": "2024-01-01T12:00:00+00:00",
                    }
                ],
                "metadata": {
                    "total_answers": 1,
                    "user_id": 123,
                    "company_id": None,
                    "quiz_id": None,
                    "format": "json",
                    "exported_at": "2024-01-01T12:00:00+00:00",
                },
            }
        }
    )

    data: list[QuizAnswerExportData]
    metadata: ExportMetadata
