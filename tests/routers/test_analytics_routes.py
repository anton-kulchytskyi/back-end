from datetime import date, timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_my_overall_analytics_success(
    client: AsyncClient,
    test_user_token: str,
):
    response = await client.get(
        "/analytics/me/overall",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200

    data = response.json()
    assert "correct_answers" in data
    assert "total_answers" in data
    assert "average_score" in data


@pytest.mark.asyncio
async def test_get_my_overall_analytics_unauthorized(
    client: AsyncClient,
):
    response = await client.get("/analytics/me/overall")

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_company_weekly_analytics_forbidden(
    client: AsyncClient, test_company, test_member_token
):
    response = await client.get(
        f"/analytics/companies/{test_company.id}/users/weekly-averages",
        headers={"Authorization": f"Bearer {test_member_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_my_quiz_averages_success(
    client: AsyncClient,
    test_user_token: str,
):
    """Test GET /analytics/me/quizzes/averages"""
    from_date = date.today() - timedelta(days=30)
    to_date = date.today()

    response = await client.get(
        "/analytics/me/quizzes/averages",
        params={
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "page": 1,
            "limit": 10,
        },
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data


@pytest.mark.asyncio
async def test_get_my_quiz_averages_invalid_date_range(
    client: AsyncClient,
    test_user_token: str,
):
    """Test invalid date range (from > to)"""
    response = await client.get(
        "/analytics/me/quizzes/averages",
        params={
            "from_date": "2024-12-31",
            "to_date": "2024-01-01",
            "page": 1,
            "limit": 10,
        },
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_my_last_completions_success(
    client: AsyncClient,
    test_user_token: str,
):
    """Test GET /analytics/me/quizzes/last-completions"""
    response = await client.get(
        "/analytics/me/quizzes/last-completions",
        params={"page": 1, "limit": 10},
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_my_last_completions_unauthorized(
    client: AsyncClient,
):
    """Test unauthorized access"""
    response = await client.get(
        "/analytics/me/quizzes/last-completions",
        params={"page": 1, "limit": 10},
    )

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_company_weekly_analytics_owner_success(
    client: AsyncClient, test_company, test_user_token
):
    """Test owner can access company analytics"""
    response = await client.get(
        f"/analytics/companies/{test_company.id}/users/weekly-averages",
        headers={"Authorization": f"Bearer {test_user_token}"},
        params={"page": 1, "limit": 10},
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_company_weekly_analytics_admin_success(
    client: AsyncClient, company_with_admin, test_admin_token
):
    """Test admin can access company analytics"""
    response = await client.get(
        f"/analytics/companies/{company_with_admin.id}/users/weekly-averages",
        headers={"Authorization": f"Bearer {test_admin_token}"},
        params={"page": 1, "limit": 10},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_company_user_quiz_averages_success(
    client: AsyncClient, test_company, test_user, test_user_token
):
    """Test GET /companies/{id}/users/{user_id}/quizzes/weekly-averages"""
    response = await client.get(
        f"/analytics/companies/{test_company.id}/users/{test_user.id}/quizzes/weekly-averages",
        headers={"Authorization": f"Bearer {test_user_token}"},
        params={"page": 1, "limit": 10},
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_company_users_last_attempts_success(
    client: AsyncClient, test_company, test_user_token
):
    """Test GET /companies/{id}/users/last-attempts"""
    response = await client.get(
        f"/analytics/companies/{test_company.id}/users/last-attempts",
        headers={"Authorization": f"Bearer {test_user_token}"},
        params={"page": 1, "limit": 10},
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_company_analytics_invalid_company_id(
    client: AsyncClient, test_user_token
):
    """Test with non-existent company ID"""
    response = await client.get(
        "/analytics/companies/99999/users/weekly-averages",
        headers={"Authorization": f"Bearer {test_user_token}"},
        params={"page": 1, "limit": 10},
    )

    # assert response.status_code in (403, 404)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_company_analytics_unauthorized(client: AsyncClient, test_company):
    """Test unauthorized access to company analytics"""
    response = await client.get(
        f"/analytics/companies/{test_company.id}/users/weekly-averages",
        params={"page": 1, "limit": 10},
    )

    assert response.status_code in (401, 403)
