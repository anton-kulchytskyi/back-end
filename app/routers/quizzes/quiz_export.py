from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user, get_quiz_export_service
from app.models import User
from app.schemas.quiz.quiz_export import ExportFormat
from app.services.quiz.quiz_export_service import QuizExportService
from app.utils.export_formatter import make_csv_response, make_json_response

router = APIRouter()


@router.get("/me")
async def export_my_data(
    format: ExportFormat = Query(..., description="json or csv"),
    quiz_id: int | None = None,
    current_user: User = Depends(get_current_user),
    export_service: QuizExportService = Depends(get_quiz_export_service),
):
    answers = await export_service.export_user_data(current_user.id, quiz_id)

    if format is ExportFormat.CSV:
        return make_csv_response(answers, f"user-{current_user.id}.csv")

    return make_json_response(
        answers,
        user_id=current_user.id,
        quiz_id=quiz_id,
    )


@router.get(
    "/company/{company_id}",
    summary="Export company quiz answers",
    description="Export quiz answers for a company (admin/owner only).",
)
async def export_company_data(
    company_id: int,
    format: ExportFormat = Query(..., description="json or csv"),
    user_id: int | None = Query(None),
    quiz_id: int | None = Query(None),
    current_user: User = Depends(get_current_user),
    export_service: QuizExportService = Depends(get_quiz_export_service),
):
    """Company owner/admin exports quiz answers."""

    answers = await export_service.export_company_data(
        company_id=company_id,
        current_user_id=current_user.id,
        user_id=user_id,
        quiz_id=quiz_id,
    )

    if format is ExportFormat.CSV:
        return make_csv_response(
            answers,
            filename=f"quiz-export-company-{company_id}.csv",
        )

    return make_json_response(
        answers,
        company_id=company_id,
        user_id=user_id,
        quiz_id=quiz_id,
    )
