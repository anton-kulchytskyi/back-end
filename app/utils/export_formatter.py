import csv
import io
from typing import Any, List

from fastapi.responses import Response

from app.schemas.quiz.quiz_export import (
    ExportFormat,
    ExportMetadata,
    ExportResponse,
    QuizAnswerExportData,
)


class CSVFormatter:
    """
    Formatter for converting quiz data to CSV format.
    """

    HEADERS = [
        "user_id",
        "company_id",
        "quiz_id",
        "question_id",
        "answer_id",
        "is_correct",
        "attempt_id",
        "answered_at",
    ]

    @classmethod
    def format_to_csv(cls, items: list[QuizAnswerExportData]) -> str:
        """Convert list of RedisQuizAnswerData into a CSV string."""

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=cls.HEADERS)
        writer.writeheader()

        for item in items:
            writer.writerow(cls._row(item))

        return output.getvalue()

    @staticmethod
    def _row(item: QuizAnswerExportData) -> dict[str, Any]:
        """
        Convert RedisQuizAnswerData into a dict suitable for CSV output.

        """
        return {
            "user_id": item.user_id,
            "company_id": item.company_id,
            "quiz_id": item.quiz_id,
            "question_id": item.question_id,
            "answer_id": item.answer_id,
            "is_correct": "1" if item.is_correct else "0",
            "attempt_id": item.attempt_id,
            "answered_at": item.answered_at.isoformat(),
        }


def make_csv_response(answers: List[QuizAnswerExportData], filename: str) -> Response:
    content = CSVFormatter.format_to_csv(answers)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def make_json_response(
    answers: List[QuizAnswerExportData],
    *,
    user_id: int | None = None,
    company_id: int | None = None,
    quiz_id: int | None = None,
) -> ExportResponse:
    return ExportResponse(
        data=answers,
        metadata=ExportMetadata(
            total_answers=len(answers),
            user_id=user_id,
            company_id=company_id,
            quiz_id=quiz_id,
            format=ExportFormat.JSON,
        ),
    )
