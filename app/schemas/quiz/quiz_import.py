from typing import Literal

from pydantic import BaseModel


class QuizImportResult(BaseModel):
    title: str
    action: Literal["created", "updated"]
    quiz_id: int


class QuizImportResponse(BaseModel):
    imported: int
    results: list[QuizImportResult]
