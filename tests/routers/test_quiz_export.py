from httpx import AsyncClient


async def test_export_me_json(
    client: AsyncClient,
    test_user,
    test_user_token,
    test_quiz,
    override_dependencies_fixture,
):
    payload = {
        "answers": [
            {
                "question_id": test_quiz.questions[0].id,
                "answer_id": test_quiz.questions[0].answers[0].id,
            },
            {
                "question_id": test_quiz.questions[1].id,
                "answer_id": test_quiz.questions[1].answers[0].id,
            },
        ]
    }

    await client.post(
        f"/quiz-attempts/quizzes/{test_quiz.id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    response = await client.get(
        "/export/me?format=json", headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 200
    body = response.json()

    assert "data" in body
    assert "metadata" in body
    assert body["metadata"]["total_answers"] == 2


async def test_export_me_csv(
    client: AsyncClient,
    test_user_token,
    test_quiz,
    override_dependencies_fixture,
):
    payload = {
        "answers": [
            {
                "question_id": test_quiz.questions[0].id,
                "answer_id": test_quiz.questions[0].answers[0].id,
            },
        ]
    }
    await client.post(
        f"/quiz-attempts/quizzes/{test_quiz.id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    response = await client.get(
        "/export/me?format=csv", headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "user_id" in response.text  # header
    assert "quiz_id" in response.text


async def test_export_company_as_admin(
    client: AsyncClient,
    test_admin_token,
    company_with_admin,
    test_quiz,
    override_dependencies_fixture,
    test_user_token,
):
    payload = {
        "answers": [
            {
                "question_id": q.id,
                "answer_id": q.answers[0].id,
            }
            for q in test_quiz.questions
        ]
    }
    await client.post(
        f"/quiz-attempts/quizzes/{test_quiz.id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    response = await client.get(
        f"/export/company/{test_quiz.company_id}?format=json",
        headers={"Authorization": f"Bearer {test_admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["total_answers"] == len(test_quiz.questions)


async def test_export_company_forbidden_for_member(
    client: AsyncClient,
    test_member_token,
    company_with_member,
):
    response = await client.get(
        f"/export/company/{company_with_member.id}?format=json",
        headers={"Authorization": f"Bearer {test_member_token}"},
    )

    assert response.status_code == 403


async def test_export_company_filter_by_quiz(
    client: AsyncClient,
    test_admin_token,
    test_quiz,
    override_dependencies_fixture,
    test_user_token,
):
    payload = {
        "answers": [
            {
                "question_id": test_quiz.questions[0].id,
                "answer_id": test_quiz.questions[0].answers[0].id,
            },
        ]
    }
    await client.post(
        f"/quiz-attempts/quizzes/{test_quiz.id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    response = await client.get(
        f"/export/company/{test_quiz.company_id}?format=json&quiz_id={test_quiz.id}",
        headers={"Authorization": f"Bearer {test_admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["quiz_id"] == test_quiz.id


async def test_export_company_filter_by_user(
    client: AsyncClient,
    test_admin_token,
    test_quiz,
    override_dependencies_fixture,
    test_user,
    test_user_token,
):
    payload = {
        "answers": [
            {
                "question_id": test_quiz.questions[0].id,
                "answer_id": test_quiz.questions[0].answers[0].id,
            },
        ]
    }
    await client.post(
        f"/quiz-attempts/quizzes/{test_quiz.id}/attempt",
        json=payload,
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    response = await client.get(
        f"/export/company/{test_quiz.company_id}?format=json&user_id={test_user.id}",
        headers={"Authorization": f"Bearer {test_admin_token}"},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["user_id"] == test_user.id


async def test_export_company_wrong_quiz_rejected(
    client: AsyncClient,
    test_admin_token,
    company_with_admin,
):
    response = await client.get(
        f"/export/company/{company_with_admin.id}?format=json&quiz_id=999",
        headers={"Authorization": f"Bearer {test_admin_token}"},
    )

    assert response.status_code in (400, 404)


async def test_export_me_empty(client, test_user_token):
    response = await client.get(
        "/export/me?format=json", headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["total_answers"] == 0
