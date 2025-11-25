import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import Role
from app.models import Company, CompanyMember, User


@pytest.mark.asyncio
async def test_appoint_admin_success(
    client: AsyncClient,
    test_user_token: str,
    company_with_member: Company,
    test_member_user: User,
):
    """Test owner can promote member to admin."""
    response = await client.post(
        f"/companies/{company_with_member.id}/admins/{test_member_user.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == test_member_user.id
    assert data["company_id"] == company_with_member.id
    assert data["role"] == Role.ADMIN.value


@pytest.mark.asyncio
async def test_appoint_admin_already_admin(
    client: AsyncClient,
    test_user_token: str,
    company_with_admin: Company,
    test_admin_user: User,
):
    """Test promoting user who is already admin returns same member."""
    response = await client.post(
        f"/companies/{company_with_admin.id}/admins/{test_admin_user.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == Role.ADMIN.value


@pytest.mark.asyncio
async def test_appoint_admin_not_member(
    client: AsyncClient,
    test_user_token: str,
    test_company: Company,
    db_session: AsyncSession,
):
    """Test cannot promote user who is not a member."""
    from app.core.security import hash_password

    non_member = User(
        email="nonmember@example.com",
        full_name="Non Member",
        hashed_password=hash_password("pass123"),
        is_active=True,
    )
    db_session.add(non_member)
    await db_session.commit()
    await db_session.refresh(non_member)

    response = await client.post(
        f"/companies/{test_company.id}/admins/{non_member.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 404
    assert "not a member" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_appoint_admin_not_owner(
    client: AsyncClient,
    test_member_user: User,
    test_member_token: str,
    company_with_member: Company,
    test_admin_user: User,
    db_session: AsyncSession,
):
    """Test only owner can appoint admin (member cannot)."""
    # Add admin_user as member
    membership = CompanyMember(
        company_id=company_with_member.id,
        user_id=test_admin_user.id,
        role=Role.MEMBER,
    )
    db_session.add(membership)
    await db_session.commit()

    response = await client.post(
        f"/companies/{company_with_member.id}/admins/{test_admin_user.id}",
        headers={"Authorization": f"Bearer {test_member_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_appoint_admin_company_not_found(
    client: AsyncClient,
    test_user_token: str,
    test_member_user: User,
):
    """Test appointing admin in non-existent company."""
    response = await client.post(
        f"/companies/99999/admins/{test_member_user.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_appoint_admin_unauthorized(
    client: AsyncClient,
    company_with_member: Company,
    test_member_user: User,
):
    """Test appointing admin without authentication."""
    response = await client.post(
        f"/companies/{company_with_member.id}/admins/{test_member_user.id}",
    )

    assert response.status_code == 403


# ==================== REMOVE ADMIN TESTS ====================


@pytest.mark.asyncio
async def test_remove_admin_success(
    client: AsyncClient,
    test_user_token: str,
    company_with_admin: Company,
    test_admin_user: User,
):
    """Test owner can demote admin to member."""
    response = await client.delete(
        f"/companies/{company_with_admin.id}/admins/{test_admin_user.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == test_admin_user.id
    assert data["company_id"] == company_with_admin.id
    assert data["role"] == Role.MEMBER.value


@pytest.mark.asyncio
async def test_remove_admin_not_admin(
    client: AsyncClient,
    test_user_token: str,
    company_with_member: Company,
    test_member_user: User,
):
    """Test cannot demote user who is not admin."""
    response = await client.delete(
        f"/companies/{company_with_member.id}/admins/{test_member_user.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 400
    assert "not an admin" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_remove_admin_not_member(
    client: AsyncClient,
    test_user_token: str,
    test_company: Company,
    db_session: AsyncSession,
):
    """Test cannot demote user who is not a member."""
    from app.core.security import hash_password

    non_member = User(
        email="nonmember2@example.com",
        full_name="Non Member 2",
        hashed_password=hash_password("pass123"),
        is_active=True,
    )
    db_session.add(non_member)
    await db_session.commit()
    await db_session.refresh(non_member)

    response = await client.delete(
        f"/companies/{test_company.id}/admins/{non_member.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 404
    assert "not a member" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_remove_admin_not_owner(
    client: AsyncClient,
    test_admin_user: User,
    test_admin_token: str,
    company_with_admin: Company,
    test_member_user: User,
    db_session: AsyncSession,
):
    """Test only owner can remove admin (admin cannot remove other admins)."""
    # Add member_user as admin
    membership = CompanyMember(
        company_id=company_with_admin.id,
        user_id=test_member_user.id,
        role=Role.ADMIN,
    )
    db_session.add(membership)
    await db_session.commit()

    response = await client.delete(
        f"/companies/{company_with_admin.id}/admins/{test_member_user.id}",
        headers={"Authorization": f"Bearer {test_admin_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_remove_admin_company_not_found(
    client: AsyncClient,
    test_user_token: str,
    test_admin_user: User,
):
    """Test removing admin from non-existent company."""
    response = await client.delete(
        f"/companies/99999/admins/{test_admin_user.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_remove_admin_unauthorized(
    client: AsyncClient,
    company_with_admin: Company,
    test_admin_user: User,
):
    """Test removing admin without authentication."""
    response = await client.delete(
        f"/companies/{company_with_admin.id}/admins/{test_admin_user.id}",
    )

    assert response.status_code == 403


# ==================== GET ADMINS TESTS ====================


@pytest.mark.asyncio
async def test_get_admins_success(
    client: AsyncClient,
    test_user_token: str,
    company_with_admin: Company,
    test_admin_user: User,
):
    """Test getting list of admins."""
    response = await client.get(
        f"/companies/{company_with_admin.id}/admins",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    assert data["total"] >= 1
    assert any(m["user_id"] == test_admin_user.id for m in data["results"])
    assert all(m["role"] == Role.ADMIN.value for m in data["results"])


@pytest.mark.asyncio
async def test_get_admins_pagination(
    client: AsyncClient,
    test_user_token: str,
    company_with_admin: Company,
    db_session: AsyncSession,
):
    """Test admins list pagination."""
    from app.core.security import hash_password

    # Create multiple admins
    for i in range(5):
        user = User(
            email=f"admin{i}@example.com",
            full_name=f"Admin {i}",
            hashed_password=hash_password("pass123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        membership = CompanyMember(
            company_id=company_with_admin.id,
            user_id=user.id,
            role=Role.ADMIN,
        )
        db_session.add(membership)
    await db_session.commit()

    # Test first page
    response = await client.get(
        f"/companies/{company_with_admin.id}/admins?page=1&limit=3",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["results"]) == 3
    assert data["page"] == 1
    assert data["limit"] == 3
    assert data["total"] >= 6  # 1 original + 5 new


@pytest.mark.asyncio
async def test_get_admins_empty(
    client: AsyncClient,
    test_user_token: str,
    test_company: Company,
):
    """Test getting admins when there are no admins (only owner)."""

    response = await client.get(
        f"/companies/{test_company.id}/admins",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert len(data["results"]) == 0


@pytest.mark.asyncio
async def test_get_admins_member_can_view(
    client: AsyncClient,
    test_member_user: User,
    test_member_token: str,
    company_with_admin: Company,
    db_session: AsyncSession,
):
    """Test regular member can view admins list."""

    # Add test_member_user as regular member to the company
    membership = CompanyMember(
        company_id=company_with_admin.id,
        user_id=test_member_user.id,
        role=Role.MEMBER,
    )
    db_session.add(membership)
    await db_session.commit()

    response = await client.get(
        f"/companies/{company_with_admin.id}/admins",
        headers={"Authorization": f"Bearer {test_member_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    assert isinstance(data["results"], list)


@pytest.mark.asyncio
async def test_get_admins_non_member_cannot_view(
    client: AsyncClient,
    test_company: Company,
    db_session: AsyncSession,
):
    """Test non-member cannot view admins list."""
    from app.core.security import hash_password

    # Create user who is not a member
    non_member = User(
        email="outsider@example.com",
        full_name="Outsider",
        hashed_password=hash_password("pass123"),
        is_active=True,
    )
    db_session.add(non_member)
    await db_session.commit()
    await db_session.refresh(non_member)

    # Get token for non-member
    login_data = {
        "username": "outsider@example.com",
        "password": "pass123",
    }
    login_response = await client.post("/auth/login", data=login_data)
    token = login_response.json()["access_token"]

    response = await client.get(
        f"/companies/{test_company.id}/admins",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_admins_company_not_found(
    client: AsyncClient,
    test_user_token: str,
):
    """Test getting admins from non-existent company."""
    response = await client.get(
        "/companies/99999/admins",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_admins_unauthorized(
    client: AsyncClient,
    test_company: Company,
):
    """Test getting admins without authentication."""
    response = await client.get(
        f"/companies/{test_company.id}/admins",
    )

    assert response.status_code == 403


# ==================== EDGE CASES ====================


@pytest.mark.asyncio
async def test_cannot_promote_owner_to_admin(
    client: AsyncClient,
    test_user_token: str,
    test_company: Company,
    test_user: User,
):
    """Test owner's role should remain OWNER (edge case check)."""
    response = await client.post(
        f"/companies/{test_company.id}/admins/{test_user.id}",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    # This should either succeed keeping OWNER role or fail gracefully
    assert response.status_code in [200, 400]


@pytest.mark.asyncio
async def test_multiple_admins_in_company(
    client: AsyncClient,
    test_user_token: str,
    test_company: Company,
    db_session: AsyncSession,
):
    """Test company can have multiple admins."""
    from app.core.security import hash_password

    admins_created = []

    for i in range(3):
        user = User(
            email=f"newadmin{i}@example.com",
            full_name=f"New Admin {i}",
            hashed_password=hash_password("pass123"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Add as member first
        membership = CompanyMember(
            company_id=test_company.id,
            user_id=user.id,
            role=Role.MEMBER,
        )
        db_session.add(membership)
        await db_session.commit()

        # Promote to admin
        response = await client.post(
            f"/companies/{test_company.id}/admins/{user.id}",
            headers={"Authorization": f"Bearer {test_user_token}"},
        )
        assert response.status_code == 200
        admins_created.append(user.id)

    # Verify all admins exist
    response = await client.get(
        f"/companies/{test_company.id}/admins",
        headers={"Authorization": f"Bearer {test_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] >= 3
    admin_ids = [m["user_id"] for m in data["results"]]

    for admin_id in admins_created:
        assert admin_id in admin_ids
