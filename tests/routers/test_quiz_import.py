"""Tests for POST /companies/{company_id}/quizzes/import endpoint."""

import io

import pytest_asyncio
from httpx import AsyncClient
from openpyxl import Workbook
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Company, User

# ============================================================================
# Helpers
# ============================================================================


def make_xlsx(rows: list[tuple]) -> bytes:
    """Build an in-memory .xlsx file from a list of row tuples.

    Row 0 is always the header:
      quiz_title | quiz_description | question |
      answer_1 | is_correct_1 | answer_2 | is_correct_2 |
      answer_3 | is_correct_3 | answer_4 | is_correct_4
    """
    wb = Workbook()
    ws = wb.active
    ws.append(
        [
            "quiz_title",
            "quiz_description",
            "question",
            "answer_1",
            "is_correct_1",
            "answer_2",
            "is_correct_2",
            "answer_3",
            "is_correct_3",
            "answer_4",
            "is_correct_4",
        ]
    )
    for row in rows:
        ws.append(list(row))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _two_question_xlsx(title: str = "Import Quiz", description: str = "Desc") -> bytes:
    """Minimal valid xlsx with two questions."""
    return make_xlsx(
        [
            (
                title,
                description,
                "Q1?",
                "A1",
                True,
                "A2",
                False,
                None,
                None,
                None,
                None,
            ),
            (
                title,
                description,
                "Q2?",
                "B1",
                True,
                "B2",
                False,
                None,
                None,
                None,
                None,
            ),
        ]
    )


# ============================================================================
# Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def owner_token(client: AsyncClient, test_user: User) -> str:
    """test_user is already owner of test_company — reuse their token."""
    response = await client.post(
        "/auth/login",
        data={"username": test_user.email, "password": "testpassword123"},
    )
    return response.json()["access_token"]


# ============================================================================
# Tests
# ============================================================================


async def test_import_creates_new_quiz(
    client: AsyncClient,
    test_company: Company,
    owner_token: str,
):
    """A quiz that doesn't exist yet should be created."""
    xlsx = _two_question_xlsx("Brand New Quiz")

    response = await client.post(
        f"/companies/{test_company.id}/quizzes/import",
        files={
            "file": (
                "quizzes.xlsx",
                xlsx,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 1
    assert data["results"][0]["action"] == "created"
    assert data["results"][0]["title"] == "Brand New Quiz"
    assert isinstance(data["results"][0]["quiz_id"], int)


async def test_import_updates_existing_quiz(
    client: AsyncClient,
    test_company: Company,
    owner_token: str,
):
    """A quiz with the same title should be updated, not duplicated."""
    title = "Update Me Quiz"
    xlsx = _two_question_xlsx(title)

    # Create first
    r1 = await client.post(
        f"/companies/{test_company.id}/quizzes/import",
        files={
            "file": (
                "q.xlsx",
                xlsx,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert r1.status_code == 200
    quiz_id = r1.json()["results"][0]["quiz_id"]

    # Import again with same title but different question
    xlsx2 = make_xlsx(
        [
            (
                title,
                "Updated Desc",
                "New Q1?",
                "C1",
                True,
                "C2",
                False,
                None,
                None,
                None,
                None,
            ),
            (
                title,
                "Updated Desc",
                "New Q2?",
                "D1",
                True,
                "D2",
                False,
                None,
                None,
                None,
                None,
            ),
        ]
    )
    r2 = await client.post(
        f"/companies/{test_company.id}/quizzes/import",
        files={
            "file": (
                "q.xlsx",
                xlsx2,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["results"][0]["action"] == "updated"
    assert data["results"][0]["quiz_id"] == quiz_id


async def test_import_multiple_quizzes(
    client: AsyncClient,
    test_company: Company,
    owner_token: str,
):
    """Multiple quizzes in one file should all be imported."""
    xlsx = make_xlsx(
        [
            (
                "Quiz Alpha",
                "Desc",
                "Q1?",
                "A",
                True,
                "B",
                False,
                None,
                None,
                None,
                None,
            ),
            (
                "Quiz Alpha",
                "Desc",
                "Q2?",
                "C",
                True,
                "D",
                False,
                None,
                None,
                None,
                None,
            ),
            ("Quiz Beta", "Desc", "Q1?", "E", True, "F", False, None, None, None, None),
            ("Quiz Beta", "Desc", "Q2?", "G", True, "H", False, None, None, None, None),
        ]
    )

    response = await client.post(
        f"/companies/{test_company.id}/quizzes/import",
        files={
            "file": (
                "q.xlsx",
                xlsx,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 2
    titles = {r["title"] for r in data["results"]}
    assert titles == {"Quiz Alpha", "Quiz Beta"}


async def test_import_with_four_answers(
    client: AsyncClient,
    test_company: Company,
    owner_token: str,
):
    """Questions with 4 answers should be accepted."""
    xlsx = make_xlsx(
        [
            (
                "4-Answer Quiz",
                "Desc",
                "Q1?",
                "A",
                True,
                "B",
                False,
                "C",
                False,
                "D",
                False,
            ),
            (
                "4-Answer Quiz",
                "Desc",
                "Q2?",
                "E",
                False,
                "F",
                True,
                "G",
                False,
                "H",
                False,
            ),
        ]
    )

    response = await client.post(
        f"/companies/{test_company.id}/quizzes/import",
        files={
            "file": (
                "q.xlsx",
                xlsx,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 200
    assert response.json()["imported"] == 1


async def test_import_requires_auth(
    client: AsyncClient,
    test_company: Company,
):
    """Unauthenticated request must be rejected."""
    xlsx = _two_question_xlsx()

    response = await client.post(
        f"/companies/{test_company.id}/quizzes/import",
        files={
            "file": (
                "q.xlsx",
                xlsx,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code in (401, 403)


async def test_import_forbidden_for_non_admin(
    client: AsyncClient,
    test_company: Company,
    db_session: AsyncSession,
):
    """A user who is not owner/admin must receive 403."""
    from app.core.security import create_access_token, hash_password

    other = User(
        email="stranger@test.com",
        full_name="Stranger",
        hashed_password=hash_password("pass123"),
        is_active=True,
    )
    db_session.add(other)
    await db_session.commit()

    token = create_access_token({"sub": other.email})
    xlsx = _two_question_xlsx()

    response = await client.post(
        f"/companies/{test_company.id}/quizzes/import",
        files={
            "file": (
                "q.xlsx",
                xlsx,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code in (401, 403)


async def test_import_empty_file_returns_error(
    client: AsyncClient,
    test_company: Company,
    owner_token: str,
):
    """An Excel file with no data rows should return an error."""
    xlsx = make_xlsx([])  # header only, no data

    response = await client.post(
        f"/companies/{test_company.id}/quizzes/import",
        files={
            "file": (
                "q.xlsx",
                xlsx,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code in (400, 422, 500)
