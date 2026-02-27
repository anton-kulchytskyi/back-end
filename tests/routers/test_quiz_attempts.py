import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Company, Quiz, QuizAnswer, QuizAttempt, QuizQuestion, User


@pytest_asyncio.fixture
async def test_hidden_company(db_session: AsyncSession) -> Company:
    """Create a hidden test company."""
    company = Company(
        name="Hidden Company",
        description="Hidden Description",
        owner_id=1,
        is_visible=False,
    )
    db_session.add(company)
    await db_session.commit()
    await db_session.refresh(company)
    return company


@pytest_asyncio.fixture
async def test_quiz(
    db_session: AsyncSession, test_company: Company, test_user: User
) -> Quiz:
    """Create a test quiz with 3 questions."""
    quiz = Quiz(
        title="Python Basics",
        description="Test your Python knowledge",
        company_id=test_company.id,
        created_by=test_user.id,
    )
    db_session.add(quiz)
    await db_session.flush()

    # Question 1: Single correct answer
    question1 = QuizQuestion(quiz_id=quiz.id, title="What is 2+2?")
    db_session.add(question1)
    await db_session.flush()

    answer1_1 = QuizAnswer(question_id=question1.id, text="3", is_correct=False)
    answer1_2 = QuizAnswer(question_id=question1.id, text="4", is_correct=True)
    answer1_3 = QuizAnswer(question_id=question1.id, text="5", is_correct=False)
    db_session.add_all([answer1_1, answer1_2, answer1_3])

    # Question 2: Single correct answer
    question2 = QuizQuestion(quiz_id=quiz.id, title="What is 3*3?")
    db_session.add(question2)
    await db_session.flush()

    answer2_1 = QuizAnswer(question_id=question2.id, text="6", is_correct=False)
    answer2_2 = QuizAnswer(question_id=question2.id, text="9", is_correct=True)
    db_session.add_all([answer2_1, answer2_2])

    # Question 3: Single correct answer
    question3 = QuizQuestion(quiz_id=quiz.id, title="What is 10/2?")
    db_session.add(question3)
    await db_session.flush()

    answer3_1 = QuizAnswer(question_id=question3.id, text="5", is_correct=True)
    answer3_2 = QuizAnswer(question_id=question3.id, text="2", is_correct=False)
    db_session.add_all([answer3_1, answer3_2])

    await db_session.commit()
    await db_session.refresh(quiz)
    return quiz


@pytest_asyncio.fixture
async def test_quiz_hidden(
    db_session: AsyncSession, test_hidden_company: Company
) -> Quiz:
    """Create a quiz in hidden company."""
    quiz = Quiz(
        title="Hidden Quiz",
        description="Quiz in hidden company",
        company_id=test_hidden_company.id,
        created_by=1,
    )
    db_session.add(quiz)
    await db_session.flush()

    question = QuizQuestion(quiz_id=quiz.id, title="Question 1")
    db_session.add(question)
    await db_session.flush()

    answer1 = QuizAnswer(question_id=question.id, text="Answer 1", is_correct=True)
    answer2 = QuizAnswer(question_id=question.id, text="Answer 2", is_correct=False)
    db_session.add_all([answer1, answer2])

    await db_session.commit()
    await db_session.refresh(quiz)
    return quiz


@pytest_asyncio.fixture
async def company_admin(db_session: AsyncSession, test_hidden_company: Company):
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
        company_id=test_hidden_company.id,
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


# ============================================================================
# TEST: Submit Quiz Attempt - Success Cases
# ============================================================================


async def test_submit_quiz_attempt_all_correct(
    client: AsyncClient,
    test_user_token: str,
    test_quiz: Quiz,
    db_session: AsyncSession,
):
    """Test submitting quiz attempt with all correct answers."""
    # Get questions and correct answers
    await db_session.refresh(test_quiz, ["questions"])
    questions = test_quiz.questions

    payload = {
        "answers": [
            {
                "question_id": questions[0].id,
                "answer_id": next(a.id for a in questions[0].answers if a.is_correct),
            },
            {
                "question_id": questions[1].id,
                "answer_id": next(a.id for a in questions[1].answers if a.is_correct),
            },
            {
                "question_id": questions[2].id,
                "answer_id": next(a.id for a in questions[2].answers if a.is_correct),
            },
        ]
    }

    response = await client.post(
        f"/quiz-attempts/quizzes/{test_quiz.id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["quiz_id"] == test_quiz.id
    assert data["company_id"] == test_quiz.company_id
    assert data["score"] == 3
    assert data["total_questions"] == 3
    assert data["percentage_score"] == 100.0
    assert data["is_completed"] is True
    assert data["completed_at"] is not None
    assert data["quiz"]["id"] == test_quiz.id
    assert data["quiz"]["title"] == "Python Basics"
    assert data["company"]["id"] == test_quiz.company_id


async def test_submit_quiz_attempt_partial_correct(
    client: AsyncClient,
    test_user_token: str,
    test_quiz: Quiz,
    db_session: AsyncSession,
):
    """Test submitting quiz with 2 out of 3 correct answers."""
    await db_session.refresh(test_quiz, ["questions"])
    questions = test_quiz.questions

    payload = {
        "answers": [
            {
                "question_id": questions[0].id,
                "answer_id": next(a.id for a in questions[0].answers if a.is_correct),
            },
            {
                "question_id": questions[1].id,
                "answer_id": next(
                    a.id for a in questions[1].answers if not a.is_correct
                ),  # Wrong answer
            },
            {
                "question_id": questions[2].id,
                "answer_id": next(a.id for a in questions[2].answers if a.is_correct),
            },
        ]
    }

    response = await client.post(
        f"/quiz-attempts/quizzes/{test_quiz.id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["score"] == 2
    assert data["total_questions"] == 3
    assert data["percentage_score"] == pytest.approx(66.67, rel=0.01)
    assert data["is_completed"] is True


async def test_submit_quiz_attempt_all_wrong(
    client: AsyncClient,
    test_user_token: str,
    test_quiz: Quiz,
    db_session: AsyncSession,
):
    """Test submitting quiz with all wrong answers."""
    await db_session.refresh(test_quiz, ["questions"])
    questions = test_quiz.questions

    payload = {
        "answers": [
            {
                "question_id": questions[0].id,
                "answer_id": next(
                    a.id for a in questions[0].answers if not a.is_correct
                ),
            },
            {
                "question_id": questions[1].id,
                "answer_id": next(
                    a.id for a in questions[1].answers if not a.is_correct
                ),
            },
            {
                "question_id": questions[2].id,
                "answer_id": next(
                    a.id for a in questions[2].answers if not a.is_correct
                ),
            },
        ]
    }

    response = await client.post(
        f"/quiz-attempts/quizzes/{test_quiz.id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["score"] == 0
    assert data["total_questions"] == 3
    assert data["percentage_score"] == 0.0


# ============================================================================
# TEST: Submit Quiz Attempt - Validation Errors
# ============================================================================


async def test_submit_quiz_attempt_hidden_company(
    client: AsyncClient,
    test_user_token: str,
    test_quiz_hidden: Quiz,
    db_session: AsyncSession,
):
    """Test cannot submit quiz from hidden company."""
    await db_session.refresh(test_quiz_hidden, ["questions"])
    questions = test_quiz_hidden.questions

    payload = {
        "answers": [
            {
                "question_id": questions[0].id,
                "answer_id": questions[0].answers[0].id,
            },
        ]
    }

    response = await client.post(
        f"/quiz-attempts/quizzes/{test_quiz_hidden.id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 403


async def test_submit_hidden_company_as_admin(
    client: AsyncClient,
    company_admin_token: str,
    test_quiz_hidden: Quiz,
    db_session: AsyncSession,
):
    """Admin/owner should be able to submit quiz from hidden company."""
    await db_session.refresh(test_quiz_hidden, ["questions"])
    q = test_quiz_hidden.questions[0]

    payload = {
        "answers": [
            {"question_id": q.id, "answer_id": q.answers[0].id},
        ]
    }

    response = await client.post(
        f"/quiz-attempts/quizzes/{test_quiz_hidden.id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {company_admin_token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["quiz_id"] == test_quiz_hidden.id


async def test_submit_quiz_attempt_unauthorized(
    client: AsyncClient,
    test_quiz: Quiz,
    db_session: AsyncSession,
):
    """Test cannot submit quiz without authentication."""
    await db_session.refresh(test_quiz, ["questions"])
    questions = test_quiz.questions

    payload = {
        "answers": [
            {"question_id": questions[0].id, "answer_id": questions[0].answers[0].id},
            {"question_id": questions[1].id, "answer_id": questions[1].answers[0].id},
            {"question_id": questions[2].id, "answer_id": questions[2].answers[0].id},
        ]
    }

    response = await client.post(
        f"/quiz-attempts/quizzes/{test_quiz.id}/attempt",
        json=payload,
    )

    assert response.status_code in (401, 403)


async def test_submit_quiz_attempt_missing_answers(
    client: AsyncClient,
    test_user_token: str,
    test_quiz: Quiz,
    db_session: AsyncSession,
):
    """Test validation: must answer all questions."""
    await db_session.refresh(test_quiz, ["questions"])
    questions = test_quiz.questions

    # Only answer 2 out of 3 questions
    payload = {
        "answers": [
            {"question_id": questions[0].id, "answer_id": questions[0].answers[0].id},
            {"question_id": questions[1].id, "answer_id": questions[1].answers[0].id},
        ]
    }

    response = await client.post(
        f"/quiz-attempts/quizzes/{test_quiz.id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 400
    assert "must answer all" in response.json()["detail"].lower()


async def test_submit_quiz_attempt_duplicate_question(
    client: AsyncClient,
    test_user_token: str,
    test_quiz: Quiz,
    db_session: AsyncSession,
):
    """Test validation: cannot answer same question twice."""
    await db_session.refresh(test_quiz, ["questions"])
    questions = test_quiz.questions

    payload = {
        "answers": [
            {"question_id": questions[0].id, "answer_id": questions[0].answers[0].id},
            {
                "question_id": questions[0].id,
                "answer_id": questions[0].answers[1].id,
            },  # Duplicate!
            {"question_id": questions[2].id, "answer_id": questions[2].answers[0].id},
        ]
    }

    response = await client.post(
        f"/quiz-attempts/quizzes/{test_quiz.id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 400
    assert "same question multiple times" in response.json()["detail"].lower()


async def test_submit_quiz_attempt_invalid_question_id(
    client: AsyncClient,
    test_user_token: str,
    test_quiz: Quiz,
    db_session: AsyncSession,
):
    """Test validation: question must belong to quiz."""
    await db_session.refresh(test_quiz, ["questions"])
    questions = test_quiz.questions

    payload = {
        "answers": [
            {
                "question_id": 99999,
                "answer_id": questions[0].answers[0].id,
            },  # Invalid question
            {"question_id": questions[1].id, "answer_id": questions[1].answers[0].id},
            {"question_id": questions[2].id, "answer_id": questions[2].answers[0].id},
        ]
    }

    response = await client.post(
        f"/quiz-attempts/quizzes/{test_quiz.id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 400
    assert "does not belong" in response.json()["detail"].lower()


async def test_submit_quiz_attempt_invalid_answer_id(
    client: AsyncClient,
    test_user_token: str,
    test_quiz: Quiz,
    db_session: AsyncSession,
):
    """Test validation: answer must belong to question."""
    await db_session.refresh(test_quiz, ["questions"])
    questions = test_quiz.questions

    payload = {
        "answers": [
            {"question_id": questions[0].id, "answer_id": 99999},  # Invalid answer
            {"question_id": questions[1].id, "answer_id": questions[1].answers[0].id},
            {"question_id": questions[2].id, "answer_id": questions[2].answers[0].id},
        ]
    }

    response = await client.post(
        f"/quiz-attempts/quizzes/{test_quiz.id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 400
    assert "does not belong" in response.json()["detail"].lower()


async def test_submit_quiz_attempt_quiz_not_found(
    client: AsyncClient,
    test_user_token: str,
):
    """Test quiz not found."""
    payload = {
        "answers": [
            {"question_id": 1, "answer_id": 1},
        ]
    }

    response = await client.post(
        "/quiz-attempts/quizzes/99999/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 404


# ============================================================================
# TEST: Get User Statistics
# ============================================================================


async def test_get_user_statistics_no_attempts(
    client: AsyncClient,
    test_user_token: str,
):
    """Test statistics with no quiz attempts."""
    response = await client.get(
        "/quiz-attempts/users/me/statistics",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["global_average"] is None
    assert data["company_average"] is None
    assert data["total_quizzes_taken"] == 0
    assert data["last_attempt_at"] is None


# ============================================================================
# TEST: Get Quiz History
# ============================================================================


async def test_get_quiz_history_empty(
    client: AsyncClient,
    test_user_token: str,
):
    """Test quiz history with no attempts."""
    response = await client.get(
        "/quiz-attempts/users/me/history",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert data["page"] == 1
    assert data["limit"] == 10
    assert len(data["results"]) == 0


async def test_get_quiz_history_with_pagination(
    client: AsyncClient,
    test_user_token: str,
    test_user: User,
    test_quiz: Quiz,
    db_session: AsyncSession,
):
    """Test quiz history pagination."""
    # Create 15 attempts
    for i in range(15):
        attempt = QuizAttempt(
            user_id=test_user.id,
            quiz_id=test_quiz.id,
            company_id=test_quiz.company_id,
            score=i,
            total_questions=10,
        )
        attempt.mark_completed()
        db_session.add(attempt)

    await db_session.commit()

    # Page 1
    response = await client.get(
        "/quiz-attempts/users/me/history?page=1&limit=10",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 15
    assert data["page"] == 1
    assert data["limit"] == 10
    assert data["total_pages"] == 2
    assert len(data["results"]) == 10

    # Page 2
    response = await client.get(
        "/quiz-attempts/users/me/history?page=2&limit=10",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 2
    assert len(data["results"]) == 5


async def test_get_quiz_history_with_company_filter(
    client: AsyncClient,
    test_user_token: str,
    test_user: User,
    test_company: Company,
    test_hidden_company: Company,
    test_quiz: Quiz,
    db_session: AsyncSession,
):
    """Test quiz history filtered by company."""
    # Create quiz in hidden company
    quiz2 = Quiz(
        title="Quiz 2",
        description="Another quiz",
        company_id=test_hidden_company.id,
        created_by=1,
    )
    db_session.add(quiz2)
    await db_session.flush()

    # Create attempts in both companies
    attempt1 = QuizAttempt(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        company_id=test_company.id,
        score=5,
        total_questions=10,
    )
    attempt1.mark_completed()
    db_session.add(attempt1)

    attempt2 = QuizAttempt(
        user_id=test_user.id,
        quiz_id=quiz2.id,
        company_id=test_hidden_company.id,
        score=7,
        total_questions=10,
    )
    attempt2.mark_completed()
    db_session.add(attempt2)

    await db_session.commit()

    # Filter by test_company
    response = await client.get(
        f"/quiz-attempts/users/me/history?company_id={test_company.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert data["results"][0]["company_id"] == test_company.id


async def test_get_quiz_history_with_quiz_filter(
    client: AsyncClient,
    test_user_token: str,
    test_user: User,
    test_quiz: Quiz,
    db_session: AsyncSession,
):
    """Test quiz history filtered by quiz."""
    # Create 2 different quizzes
    quiz2 = Quiz(
        title="Quiz 2",
        description="Another quiz",
        company_id=test_quiz.company_id,
        created_by=1,
    )
    db_session.add(quiz2)
    await db_session.flush()

    # Create attempts for both quizzes
    attempt1 = QuizAttempt(
        user_id=test_user.id,
        quiz_id=test_quiz.id,
        company_id=test_quiz.company_id,
        score=5,
        total_questions=10,
    )
    attempt1.mark_completed()
    db_session.add(attempt1)

    attempt2 = QuizAttempt(
        user_id=test_user.id,
        quiz_id=quiz2.id,
        company_id=test_quiz.company_id,
        score=7,
        total_questions=10,
    )
    attempt2.mark_completed()
    db_session.add(attempt2)

    await db_session.commit()

    # Filter by test_quiz
    response = await client.get(
        f"/quiz-attempts/users/me/history?quiz_id={test_quiz.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert data["results"][0]["quiz_id"] == test_quiz.id


async def test_get_quiz_history_unauthorized(
    client: AsyncClient,
):
    """Test cannot get history without authentication."""
    response = await client.get("/quiz-attempts/users/me/history")

    assert response.status_code in (401, 403)


# ============================================================================
# TEST: Average Calculation Logic
# ============================================================================


async def test_get_user_statistics_with_attempts(
    client: AsyncClient,
    test_user_token: str,
    test_user: User,
    db_session: AsyncSession,
):
    """Test statistics calculation with multiple attempts."""

    # Create company
    company = Company(
        name="Test Company",
        description="Test",
        owner_id=test_user.id,
        is_visible=True,
    )
    db_session.add(company)
    await db_session.flush()

    # Create quiz1 with 10 questions (will answer 8/10 correct)
    quiz1 = Quiz(
        title="Math Quiz 1",
        description="10 questions",
        company_id=company.id,
        created_by=test_user.id,
    )
    db_session.add(quiz1)
    await db_session.flush()

    # Add 10 questions to quiz1
    quiz1_questions = []
    for i in range(10):
        question = QuizQuestion(quiz_id=quiz1.id, title=f"Question {i+1}")
        db_session.add(question)
        await db_session.flush()

        answer_correct = QuizAnswer(
            question_id=question.id, text="Correct", is_correct=True
        )
        answer_wrong = QuizAnswer(
            question_id=question.id, text="Wrong", is_correct=False
        )
        db_session.add_all([answer_correct, answer_wrong])
        await db_session.flush()

        quiz1_questions.append(
            {
                "question_id": question.id,
                "correct_id": answer_correct.id,
                "wrong_id": answer_wrong.id,
            }
        )

    await db_session.commit()

    # Submit quiz1: 8/10 correct
    payload1 = {
        "answers": [
            {
                "question_id": q["question_id"],
                "answer_id": q["correct_id"] if i < 8 else q["wrong_id"],
            }
            for i, q in enumerate(quiz1_questions)
        ]
    }

    response1 = await client.post(
        f"/quiz-attempts/quizzes/{quiz1.id}/attempt",
        json=payload1,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert response1.status_code == 201
    assert response1.json()["score"] == 8
    assert response1.json()["total_questions"] == 10

    # Create quiz2 with 8 questions (will answer 6/8 correct)
    quiz2 = Quiz(
        title="Math Quiz 2",
        description="8 questions",
        company_id=company.id,
        created_by=test_user.id,
    )
    db_session.add(quiz2)
    await db_session.flush()

    # Add 8 questions to quiz2
    quiz2_questions = []
    for i in range(8):
        question = QuizQuestion(quiz_id=quiz2.id, title=f"Question {i+1}")
        db_session.add(question)
        await db_session.flush()

        answer_correct = QuizAnswer(
            question_id=question.id, text="Correct", is_correct=True
        )
        answer_wrong = QuizAnswer(
            question_id=question.id, text="Wrong", is_correct=False
        )
        db_session.add_all([answer_correct, answer_wrong])
        await db_session.flush()

        quiz2_questions.append(
            {
                "question_id": question.id,
                "correct_id": answer_correct.id,
                "wrong_id": answer_wrong.id,
            }
        )

    await db_session.commit()

    # Submit quiz2: 6/8 correct
    payload2 = {
        "answers": [
            {
                "question_id": q["question_id"],
                "answer_id": q["correct_id"] if i < 6 else q["wrong_id"],
            }
            for i, q in enumerate(quiz2_questions)
        ]
    }

    response2 = await client.post(
        f"/quiz-attempts/quizzes/{quiz2.id}/attempt",
        json=payload2,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert response2.status_code == 201
    assert response2.json()["score"] == 6
    assert response2.json()["total_questions"] == 8

    # Now check statistics
    response = await client.get(
        "/quiz-attempts/users/me/statistics",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Global average: (8+6)/(10+8) = 14/18 = 77.78%
    assert data["global_average"] == pytest.approx(77.78, rel=0.01)
    assert data["total_quizzes_taken"] == 2
    assert data["last_attempt_at"] is not None


async def test_get_user_statistics_with_company_filter(
    client: AsyncClient,
    test_user_token: str,
    test_user: User,
    db_session: AsyncSession,
):
    """Test statistics with company filter."""

    # Create company
    company = Company(
        name="Test Company",
        description="Test",
        owner_id=test_user.id,
        is_visible=True,
    )
    db_session.add(company)
    await db_session.flush()

    # Create quiz with 10 questions
    quiz = Quiz(
        title="Test Quiz",
        description="10 questions",
        company_id=company.id,
        created_by=test_user.id,
    )
    db_session.add(quiz)
    await db_session.flush()

    # Add 10 questions
    quiz_questions = []
    for i in range(10):
        question = QuizQuestion(quiz_id=quiz.id, title=f"Question {i+1}")
        db_session.add(question)
        await db_session.flush()

        answer_correct = QuizAnswer(
            question_id=question.id, text="Correct", is_correct=True
        )
        answer_wrong = QuizAnswer(
            question_id=question.id, text="Wrong", is_correct=False
        )
        db_session.add_all([answer_correct, answer_wrong])
        await db_session.flush()

        quiz_questions.append(
            {
                "question_id": question.id,
                "correct_id": answer_correct.id,
                "wrong_id": answer_wrong.id,
            }
        )

    await db_session.commit()

    # Submit quiz: 7/10 correct
    payload = {
        "answers": [
            {
                "question_id": q["question_id"],
                "answer_id": q["correct_id"] if i < 7 else q["wrong_id"],
            }
            for i, q in enumerate(quiz_questions)
        ]
    }

    response_submit = await client.post(
        f"/quiz-attempts/quizzes/{quiz.id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert response_submit.status_code == 201
    assert response_submit.json()["score"] == 7

    # Check statistics with company filter
    response = await client.get(
        f"/quiz-attempts/users/me/statistics?company_id={company.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["global_average"] == pytest.approx(70.0, rel=0.01)
    assert data["company_average"] == pytest.approx(70.0, rel=0.01)
    assert data["total_quizzes_taken"] == 1


async def test_average_calculation_correct_formula(
    client: AsyncClient,
    test_user_token: str,
    test_user: User,
    db_session: AsyncSession,
):
    """
    Test that average is calculated correctly.

    Formula: (total_correct / total_questions) * 100
    NOT: (quiz1_percentage + quiz2_percentage) / 2
    """

    # Create company
    company = Company(
        name="Test Company",
        description="Test",
        owner_id=test_user.id,
        is_visible=True,
    )
    db_session.add(company)
    await db_session.flush()

    # Create quiz1: 10 questions (will get 8/10 = 80%)
    quiz1 = Quiz(
        title="Quiz 1",
        description="10 questions",
        company_id=company.id,
        created_by=test_user.id,
    )
    db_session.add(quiz1)
    await db_session.flush()

    quiz1_questions = []
    for i in range(10):
        question = QuizQuestion(quiz_id=quiz1.id, title=f"Q{i+1}")
        db_session.add(question)
        await db_session.flush()

        answer_correct = QuizAnswer(
            question_id=question.id, text="Correct", is_correct=True
        )
        answer_wrong = QuizAnswer(
            question_id=question.id, text="Wrong", is_correct=False
        )
        db_session.add_all([answer_correct, answer_wrong])
        await db_session.flush()

        quiz1_questions.append(
            {
                "question_id": question.id,
                "correct_id": answer_correct.id,
                "wrong_id": answer_wrong.id,
            }
        )

    await db_session.commit()

    # Submit quiz1: 8/10 correct
    payload1 = {
        "answers": [
            {
                "question_id": q["question_id"],
                "answer_id": q["correct_id"] if i < 8 else q["wrong_id"],
            }
            for i, q in enumerate(quiz1_questions)
        ]
    }

    response1 = await client.post(
        f"/quiz-attempts/quizzes/{quiz1.id}/attempt",
        json=payload1,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert response1.status_code == 201

    # Create quiz2: 8 questions (will get 6/8 = 75%)
    quiz2 = Quiz(
        title="Quiz 2",
        description="8 questions",
        company_id=company.id,
        created_by=test_user.id,
    )
    db_session.add(quiz2)
    await db_session.flush()

    quiz2_questions = []
    for i in range(8):
        question = QuizQuestion(quiz_id=quiz2.id, title=f"Q{i+1}")
        db_session.add(question)
        await db_session.flush()

        answer_correct = QuizAnswer(
            question_id=question.id, text="Correct", is_correct=True
        )
        answer_wrong = QuizAnswer(
            question_id=question.id, text="Wrong", is_correct=False
        )
        db_session.add_all([answer_correct, answer_wrong])
        await db_session.flush()

        quiz2_questions.append(
            {
                "question_id": question.id,
                "correct_id": answer_correct.id,
                "wrong_id": answer_wrong.id,
            }
        )

    await db_session.commit()

    # Submit quiz2: 6/8 correct
    payload2 = {
        "answers": [
            {
                "question_id": q["question_id"],
                "answer_id": q["correct_id"] if i < 6 else q["wrong_id"],
            }
            for i, q in enumerate(quiz2_questions)
        ]
    }

    response2 = await client.post(
        f"/quiz-attempts/quizzes/{quiz2.id}/attempt",
        json=payload2,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )
    assert response2.status_code == 201

    # Check statistics
    response = await client.get(
        "/quiz-attempts/users/me/statistics",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Correct calculation: (8+6)/(10+8) = 14/18 = 77.78%
    # WRONG would be: (80+75)/2 = 77.5%
    assert data["global_average"] == pytest.approx(77.78, rel=0.01)
    assert abs(data["global_average"] - 77.78) < abs(data["global_average"] - 77.5)
