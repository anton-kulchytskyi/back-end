"""Tests for quiz endpoints."""

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Company, Quiz, User

# Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def test_quiz(
    db_session: AsyncSession, test_company: Company, test_user: User
) -> Quiz:
    """Create test quiz with questions and answers."""
    from app.models import QuizAnswer, QuizQuestion

    quiz = Quiz(
        title="Python Basics",
        description="Test your Python knowledge",
        company_id=test_company.id,
        created_by=test_user.id,
    )
    db_session.add(quiz)
    await db_session.flush()

    question1 = QuizQuestion(quiz_id=quiz.id, title="What is Python?")
    db_session.add(question1)
    await db_session.flush()

    answers1 = [
        QuizAnswer(
            question_id=question1.id, text="Programming language", is_correct=True
        ),
        QuizAnswer(question_id=question1.id, text="Snake", is_correct=False),
        QuizAnswer(question_id=question1.id, text="Food", is_correct=False),
    ]
    db_session.add_all(answers1)

    question2 = QuizQuestion(quiz_id=quiz.id, title="Who created Python?")
    db_session.add(question2)
    await db_session.flush()

    answers2 = [
        QuizAnswer(question_id=question2.id, text="Guido van Rossum", is_correct=True),
        QuizAnswer(question_id=question2.id, text="Linus Torvalds", is_correct=False),
    ]
    db_session.add_all(answers2)

    await db_session.commit()
    await db_session.refresh(quiz)
    return quiz


@pytest_asyncio.fixture
async def company_admin(db_session: AsyncSession, test_company: Company):
    from app.core.security import hash_password
    from app.enums import Role
    from app.models import CompanyMember, User

    admin = User(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=hash_password("adminpass123"),
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()

    member = CompanyMember(
        company_id=test_company.id,
        user_id=admin.id,
        role=Role.ADMIN,
    )
    db_session.add(member)

    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def company_admin_token(client: AsyncClient, company_admin: User):
    login_data = {
        "username": company_admin.email,
        "password": "adminpass123",
    }
    response = await client.post("/auth/login", data=login_data)
    return response.json()["access_token"]


@pytest_asyncio.fixture
def valid_quiz_data() -> dict:
    """Valid quiz creation data."""
    return {
        "title": "JavaScript Basics",
        "description": "Test your JavaScript knowledge",
        "questions": [
            {
                "title": "What is JavaScript?",
                "answers": [
                    {"text": "Programming language", "is_correct": True},
                    {"text": "Java", "is_correct": False},
                    {"text": "Coffee", "is_correct": False},
                ],
            },
            {
                "title": "What is Node.js?",
                "answers": [
                    {"text": "JavaScript runtime", "is_correct": True},
                    {"text": "Framework", "is_correct": False},
                ],
            },
        ],
    }


# ============================================================================
# TESTS
# ============================================================================


async def test_create_quiz_success(
    client: AsyncClient,
    test_company: Company,
    test_user_token: str,
    valid_quiz_data: dict,
):
    """Test successful quiz creation."""
    response = await client.post(
        f"/companies/{test_company.id}/quizzes",
        json=valid_quiz_data,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["title"] == valid_quiz_data["title"]
    assert data["description"] == valid_quiz_data["description"]
    assert data["company_id"] == test_company.id
    assert data["total_questions_count"] == 2

    assert len(data["questions"]) == 2
    assert data["questions"][0]["title"] == "What is JavaScript?"
    assert len(data["questions"][0]["answers"]) == 3

    assert data["questions"][0]["answers"][0]["is_correct"] is True
    assert data["questions"][0]["answers"][1]["is_correct"] is False


async def test_create_quiz_without_auth(
    client: AsyncClient, test_company: Company, valid_quiz_data: dict
):
    """Test quiz creation without authentication."""
    response = await client.post(
        f"/companies/{test_company.id}/quizzes",
        json=valid_quiz_data,
    )

    assert response.status_code in (401, 403)


async def test_create_quiz_not_owner_or_admin(
    client: AsyncClient,
    test_company: Company,
    db_session: AsyncSession,
):
    """Test quiz creation by non-owner/admin user."""

    from app.core.security import hash_password

    other_user = User(
        email="other@example.com",
        full_name="Other User",
        hashed_password=hash_password("password123"),
    )
    db_session.add(other_user)
    await db_session.commit()

    from app.core.security import create_access_token

    other_token = create_access_token({"sub": other_user.email})

    response = await client.post(
        f"/companies/{test_company.id}/quizzes",
        json={
            "title": "Test",
            "description": "Test",
            "questions": [
                {
                    "title": "Q1",
                    "answers": [
                        {"text": "A1", "is_correct": True},
                        {"text": "A2", "is_correct": False},
                    ],
                },
                {
                    "title": "Q2",
                    "answers": [
                        {"text": "A1", "is_correct": True},
                        {"text": "A2", "is_correct": False},
                    ],
                },
            ],
        },
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code in (401, 403)


async def test_create_quiz_validation_min_questions(
    client: AsyncClient,
    test_company: Company,
    test_user_token: str,
):
    """Test quiz creation with less than 2 questions."""
    response = await client.post(
        f"/companies/{test_company.id}/quizzes",
        json={
            "title": "Test",
            "description": "Test",
            "questions": [
                {
                    "title": "Only one question",
                    "answers": [
                        {"text": "A1", "is_correct": True},
                        {"text": "A2", "is_correct": False},
                    ],
                }
            ],
        },
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 422


async def test_create_quiz_validation_min_answers(
    client: AsyncClient,
    test_company: Company,
    test_user_token: str,
):
    """Test quiz creation with less than 2 answers per question."""
    response = await client.post(
        f"/companies/{test_company.id}/quizzes",
        json={
            "title": "Test",
            "description": "Test",
            "questions": [
                {
                    "title": "Q1",
                    "answers": [
                        {"text": "Only one answer", "is_correct": True},
                    ],
                },
                {
                    "title": "Q2",
                    "answers": [
                        {"text": "A1", "is_correct": True},
                        {"text": "A2", "is_correct": False},
                    ],
                },
            ],
        },
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 422


async def test_create_quiz_validation_no_correct_answer(
    client: AsyncClient,
    test_company: Company,
    test_user_token: str,
):
    """Test quiz creation with no correct answers."""
    response = await client.post(
        f"/companies/{test_company.id}/quizzes",
        json={
            "title": "Test",
            "description": "Test",
            "questions": [
                {
                    "title": "Q1",
                    "answers": [
                        {"text": "A1", "is_correct": False},
                        {"text": "A2", "is_correct": False},
                    ],
                },
                {
                    "title": "Q2",
                    "answers": [
                        {"text": "A1", "is_correct": True},
                        {"text": "A2", "is_correct": False},
                    ],
                },
            ],
        },
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 422


async def test_get_company_quizzes(
    client: AsyncClient,
    test_company: Company,
    test_quiz: Quiz,
):
    """Test getting company quizzes list."""
    response = await client.get(f"/companies/{test_company.id}/quizzes")

    assert response.status_code == 200
    data = response.json()

    assert data["total"] >= 1
    assert data["page"] == 1
    assert data["limit"] == 10
    assert len(data["results"]) >= 1

    quiz_data = data["results"][0]
    assert quiz_data["id"] == test_quiz.id
    assert quiz_data["title"] == test_quiz.title

    assert "questions" not in quiz_data


async def test_get_company_quizzes_pagination(
    client: AsyncClient,
    test_company: Company,
):
    """Test quizzes list pagination."""
    response = await client.get(f"/companies/{test_company.id}/quizzes?page=1&limit=5")

    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 5


async def test_get_company_quizzes_empty(
    client: AsyncClient,
    test_company: Company,
):
    """Test getting quizzes for company without quizzes."""

    response = await client.get("/companies/999/quizzes")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["results"]) == 0


async def test_get_quiz_detail(
    client: AsyncClient,
    test_company: Company,
    test_quiz: Quiz,
    company_admin_token: str,
):
    """Test getting quiz details with questions and answers."""
    response = await client.get(
        f"/companies/{test_company.id}/quizzes/{test_quiz.id}",
        headers={"Authorization": f"Bearer {company_admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == test_quiz.id
    assert data["title"] == test_quiz.title
    assert data["company_id"] == test_company.id

    assert len(data["questions"]) == 2

    assert len(data["questions"][0]["answers"]) == 3
    assert "is_correct" in data["questions"][0]["answers"][0]


async def test_get_quiz_not_found(
    client: AsyncClient,
    test_company: Company,
    test_user_token: str,
):
    """Test getting non-existent quiz."""
    response = await client.get(
        f"/companies/{test_company.id}/quizzes/99999",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 404


async def test_get_quiz_for_taking(
    client: AsyncClient,
    test_company: Company,
    test_quiz: Quiz,
    test_user_token: str,
):
    """Test getting quiz for taking (without is_correct)."""
    response = await client.get(
        f"/companies/{test_company.id}/quizzes/{test_quiz.id}/take",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == test_quiz.id
    assert data["title"] == test_quiz.title

    assert len(data["questions"]) == 2

    answers = data["questions"][0]["answers"]
    assert len(answers) == 3
    assert "is_correct" not in answers[0]
    assert "text" in answers[0]
    assert "id" in answers[0]


async def test_get_quiz_for_taking_requires_auth(
    client: AsyncClient,
    test_company: Company,
    test_quiz: Quiz,
):
    """
    Ensure that accessing /take requires authentication (current_user dependency works).
    """
    response = await client.get(
        f"/companies/{test_company.id}/quizzes/{test_quiz.id}/take"
    )

    assert response.status_code in (401, 403)


async def test_update_quiz_title(
    client: AsyncClient,
    test_company: Company,
    test_quiz: Quiz,
    test_user_token: str,
):
    """Test updating quiz title only."""
    response = await client.put(
        f"/companies/{test_company.id}/quizzes/{test_quiz.id}",
        json={"title": "Updated Title"},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["title"] == "Updated Title"
    assert data["description"] == test_quiz.description
    assert len(data["questions"]) == 2


async def test_update_quiz_questions(
    client: AsyncClient,
    test_company: Company,
    test_quiz: Quiz,
    test_user_token: str,
):
    """Test updating quiz questions (replaces all)."""
    response = await client.put(
        f"/companies/{test_company.id}/quizzes/{test_quiz.id}",
        json={
            "questions": [
                {
                    "title": "New Question 1",
                    "answers": [
                        {"text": "New A1", "is_correct": True},
                        {"text": "New A2", "is_correct": False},
                    ],
                },
                {
                    "title": "New Question 2",
                    "answers": [
                        {"text": "New A1", "is_correct": True},
                        {"text": "New A2", "is_correct": False},
                    ],
                },
            ]
        },
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["questions"]) == 2
    assert data["questions"][0]["title"] == "New Question 1"
    assert data["questions"][1]["title"] == "New Question 2"


async def test_update_quiz_without_auth(
    client: AsyncClient,
    test_company: Company,
    test_quiz: Quiz,
):
    """Test updating quiz without authentication."""
    response = await client.put(
        f"/companies/{test_company.id}/quizzes/{test_quiz.id}",
        json={"title": "Updated"},
    )

    assert response.status_code in (401, 403)


async def test_update_quiz_not_found(
    client: AsyncClient,
    test_company: Company,
    test_user_token: str,
):
    """Test updating non-existent quiz."""
    response = await client.put(
        f"/companies/{test_company.id}/quizzes/99999",
        json={"title": "Updated"},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 404


async def test_delete_quiz_success(
    client: AsyncClient,
    test_company: Company,
    test_quiz: Quiz,
    company_admin_token: str,
):
    """Test successful quiz deletion."""
    response = await client.delete(
        f"/companies/{test_company.id}/quizzes/{test_quiz.id}",
        headers={"Authorization": f"Bearer {company_admin_token}"},
    )

    assert response.status_code == 204

    get_response = await client.get(
        f"/companies/{test_company.id}/quizzes/{test_quiz.id}",
        headers={"Authorization": f"Bearer {company_admin_token}"},
    )
    assert get_response.status_code == 404


async def test_delete_quiz_without_auth(
    client: AsyncClient,
    test_company: Company,
    test_quiz: Quiz,
):
    """Test deleting quiz without authentication."""
    response = await client.delete(
        f"/companies/{test_company.id}/quizzes/{test_quiz.id}"
    )

    assert response.status_code in (401, 403)


async def test_delete_quiz_not_found(
    client: AsyncClient,
    test_company: Company,
    test_user_token: str,
):
    """Test deleting non-existent quiz."""
    response = await client.delete(
        f"/companies/{test_company.id}/quizzes/99999",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 404
