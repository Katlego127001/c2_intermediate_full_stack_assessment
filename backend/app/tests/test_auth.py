"""Auth tests covering the spec's Register / Login / Logout requirements."""
import pytest

from app.tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_first_register_becomes_admin(client):
    """Spec: 'Users must be able to register'. The very first user bootstraps as admin."""
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "first@test.com",
            "password": "Password123!",
            "first_name": "First",
            "last_name": "Admin",
        },
    )
    assert res.status_code == 201
    tokens = res.json()
    assert tokens["access_token"] and tokens["refresh_token"]

    me = await client.get("/api/v1/auth/me", headers=auth_headers(tokens))
    assert me.status_code == 200
    assert me.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_subsequent_register_becomes_employee(client, admin_tokens):
    """After bootstrap, public register still works but defaults to 'employee' role."""
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "joiner@test.com",
            "password": "Password123!",
            "first_name": "New",
            "last_name": "Joiner",
        },
    )
    assert res.status_code == 201
    tokens = res.json()

    me = await client.get("/api/v1/auth/me", headers=auth_headers(tokens))
    assert me.status_code == 200
    assert me.json()["role"] == "employee"
    assert me.json()["is_active"] is True


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email(client, admin_tokens):
    """Email uniqueness is enforced."""
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@test.com",  # already taken by bootstrap admin fixture
            "password": "Password123!",
            "first_name": "Dup",
            "last_name": "Licate",
        },
    )
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_login_success_and_failure(client, admin_tokens):
    good = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Admin12345!"},
    )
    assert good.status_code == 200
    assert good.json()["access_token"]

    bad = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "wrong"},
    )
    assert bad.status_code == 401


@pytest.mark.asyncio
async def test_logout_requires_auth(client):
    unauthed = await client.post("/api/v1/auth/logout")
    assert unauthed.status_code == 401


@pytest.mark.asyncio
async def test_logout_returns_ok_with_auth(client, admin_tokens):
    res = await client.post("/api/v1/auth/logout", headers=auth_headers(admin_tokens))
    assert res.status_code == 200
    assert res.json()["message"] == "Logged out"


@pytest.mark.asyncio
async def test_change_password(client, admin_tokens):
    res = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "Admin12345!", "new_password": "NewPass1234!"},
        headers=auth_headers(admin_tokens),
    )
    assert res.status_code == 200

    bad = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "Admin12345!"},
    )
    assert bad.status_code == 401
    good = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "NewPass1234!"},
    )
    assert good.status_code == 200


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_deactivated_user_cannot_login(client, admin_tokens):
    """Spec requirement chain: deactivation must block login (RBAC integrity)."""
    # admin creates an employee
    create = await client.post(
        "/api/v1/employees",
        json={
            "email": "willbe@test.com",
            "password": "Password123!",
            "first_name": "Will",
            "last_name": "Be",
            "employment_status": "active",
        },
        headers=auth_headers(admin_tokens),
    )
    emp_id = create.json()["id"]

    # admin deactivates
    deact = await client.patch(
        f"/api/v1/employees/{emp_id}/status",
        json={"employment_status": "inactive"},
        headers=auth_headers(admin_tokens),
    )
    assert deact.status_code == 200

    # deactivated user cannot log in
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": "willbe@test.com", "password": "Password123!"},
    )
    assert res.status_code == 403
