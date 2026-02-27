"""Router for importing quizzes from Excel files."""

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.core.dependencies import get_current_user, get_quiz_import_service
from app.models import User
from app.schemas import QuizImportResponse
from app.services.quiz.quiz_import_service import QuizImportService

router = APIRouter()


@router.post(
    "",
    response_model=QuizImportResponse,
    status_code=status.HTTP_200_OK,
    summary="Import quizzes from Excel",
    description=(
        "Upload an .xlsx file to create or update quizzes in the company. "
        "Only company owner/admin can import. "
        "If a quiz with the same title already exists it will be updated; "
        "otherwise a new quiz is created."
    ),
)
async def import_quizzes(
    company_id: int,
    file: UploadFile = File(..., description="Excel file (.xlsx)"),
    current_user: User = Depends(get_current_user),
    import_service: QuizImportService = Depends(get_quiz_import_service),
) -> QuizImportResponse:
    """
    Import quizzes from an Excel file.

    **Excel format** (row 1 = header, rows 2+ = data):

    | quiz_title | quiz_description | question | answer_1 | is_correct_1 |
    | answer_2 | is_correct_2 | answer_3 | is_correct_3 | answer_4 | is_correct_4 |

    - Multiple rows with the same `quiz_title` → multiple questions for that quiz.
    - `answer_3`/`is_correct_3` and `answer_4`/`is_correct_4` columns are optional.
    - `is_correct` accepts Excel boolean (TRUE/FALSE), string, or integer (1/0).

    **Permissions**: company owner or admin only.
    """
    file_bytes = await file.read()
    return await import_service.import_quizzes(
        company_id=company_id,
        current_user=current_user,
        file_bytes=file_bytes,
    )
