"""Tests for spec-required search/filter on employees."""
import pytest

from app.tests.conftest import auth_headers


async def _create(client, admin_tokens, *, email, role="employee", department="Eng", status_="active"):
    res = await client.post(
        "/api/v1/employees",
        json={
            "email": email,
            "password": "Password123!",
            "first_name": email.split("@")[0].capitalize(),
            "last_name": "User",
            "department": department,
            "role": role,
            "employment_status": status_,
        },
        headers=auth_headers(admin_tokens),
    )
    assert res.status_code == 201, res.text
    return res.json()


@pytest.mark.asyncio
async def test_search_by_name(client, admin_tokens):
    await _create(client, admin_tokens, email="alice@test.com")
    await _create(client, admin_tokens, email="bob@test.com")
    res = await client.get("/api/v1/employees", params={"q": "alice"}, headers=auth_headers(admin_tokens))
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1 and items[0]["email"] == "alice@test.com"


@pytest.mark.asyncio
async def test_search_by_department(client, admin_tokens):
    await _create(client, admin_tokens, email="a@test.com", department="Engineering")
    await _create(client, admin_tokens, email="b@test.com", department="Design")
    # via free-text q
    res = await client.get("/api/v1/employees", params={"q": "design"}, headers=auth_headers(admin_tokens))
    assert {i["email"] for i in res.json()["items"]} == {"b@test.com"}
    # via department exact filter
    res = await client.get(
        "/api/v1/employees", params={"department": "Engineering"}, headers=auth_headers(admin_tokens)
    )
    assert {i["email"] for i in res.json()["items"]} == {"a@test.com"}


@pytest.mark.asyncio
async def test_filter_by_role(client, admin_tokens):
    await _create(client, admin_tokens, email="emp@test.com", role="employee")
    await _create(client, admin_tokens, email="admin2@test.com", role="admin")
    res = await client.get("/api/v1/employees", params={"role": "admin"}, headers=auth_headers(admin_tokens))
    emails = {i["email"] for i in res.json()["items"]}
    # bootstrap admin + admin2 should appear; no employees
    assert "admin2@test.com" in emails
    assert "emp@test.com" not in emails


@pytest.mark.asyncio
async def test_filter_by_status(client, admin_tokens):
    await _create(client, admin_tokens, email="active@test.com", status_="active")
    await _create(client, admin_tokens, email="inactive@test.com", status_="inactive")
    res = await client.get("/api/v1/employees", params={"status": "inactive"}, headers=auth_headers(admin_tokens))
    emails = {i["email"] for i in res.json()["items"]}
    assert emails == {"inactive@test.com"}
