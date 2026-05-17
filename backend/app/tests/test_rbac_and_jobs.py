import pytest

from app.tests.conftest import auth_headers


async def _create_employee(client, admin_tokens, email="emp@test.com"):
    res = await client.post(
        "/api/v1/employees",
        json={
            "email": email,
            "password": "Password123!",
            "first_name": "Em",
            "last_name": "Ployee",
            "department": "Engineering",
        },
        headers=auth_headers(admin_tokens),
    )
    assert res.status_code == 201, res.text
    return res.json()


async def _login(client, email, pw):
    res = await client.post("/api/v1/auth/login", json={"email": email, "password": pw})
    assert res.status_code == 200, res.text
    return res.json()


@pytest.mark.asyncio
async def test_employee_cannot_create_jobs(client, admin_tokens):
    emp = await _create_employee(client, admin_tokens)
    emp_tokens = await _login(client, emp["email"], "Password123!")
    res = await client.post(
        "/api/v1/jobs",
        json={"title": "Sneaky", "priority": "high"},
        headers=auth_headers(emp_tokens),
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_admin_full_job_flow_and_employee_status_only(client, admin_tokens):
    emp = await _create_employee(client, admin_tokens)
    emp_tokens = await _login(client, emp["email"], "Password123!")

    # Admin creates and assigns
    create = await client.post(
        "/api/v1/jobs",
        json={
            "title": "Ship feature",
            "description": "Build it",
            "priority": "high",
            "assigned_employee_id": emp["id"],
        },
        headers=auth_headers(admin_tokens),
    )
    assert create.status_code == 201
    job = create.json()
    assert job["assignee"]["full_name"] == "Em Ployee"

    # Employee can update status
    upd = await client.patch(
        f"/api/v1/jobs/{job['id']}/status",
        json={"status": "in_progress"},
        headers=auth_headers(emp_tokens),
    )
    assert upd.status_code == 200
    assert upd.json()["status"] == "in_progress"

    # Employee CANNOT edit other fields
    edit = await client.put(
        f"/api/v1/jobs/{job['id']}",
        json={"title": "Hijacked"},
        headers=auth_headers(emp_tokens),
    )
    assert edit.status_code == 403

    # Admin deletes
    delete = await client.delete(
        f"/api/v1/jobs/{job['id']}", headers=auth_headers(admin_tokens)
    )
    assert delete.status_code == 200

    # Job no longer visible
    listing = await client.get("/api/v1/jobs", headers=auth_headers(admin_tokens))
    assert all(j["id"] != job["id"] for j in listing.json()["items"])


@pytest.mark.asyncio
async def test_employee_only_sees_own_jobs(client, admin_tokens):
    emp_a = await _create_employee(client, admin_tokens, email="a@test.com")
    emp_b = await _create_employee(client, admin_tokens, email="b@test.com")

    # Create one job per employee
    for emp in (emp_a, emp_b):
        res = await client.post(
            "/api/v1/jobs",
            json={"title": f"Job for {emp['email']}", "assigned_employee_id": emp["id"]},
            headers=auth_headers(admin_tokens),
        )
        assert res.status_code == 201

    tokens = await _login(client, "a@test.com", "Password123!")
    listing = await client.get("/api/v1/jobs", headers=auth_headers(tokens))
    items = listing.json()["items"]
    assert len(items) == 1
    assert items[0]["assigned_employee_id"] == emp_a["id"]


@pytest.mark.asyncio
async def test_dashboard_admin_only(client, admin_tokens):
    emp = await _create_employee(client, admin_tokens)
    emp_tokens = await _login(client, emp["email"], "Password123!")

    ok = await client.get("/api/v1/dashboard/admin", headers=auth_headers(admin_tokens))
    assert ok.status_code == 200

    forbidden = await client.get(
        "/api/v1/dashboard/admin", headers=auth_headers(emp_tokens)
    )
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_employee_can_update_own_phone_only(client, admin_tokens):
    emp = await _create_employee(client, admin_tokens)
    tokens = await _login(client, emp["email"], "Password123!")

    res = await client.patch(
        "/api/v1/employees/me",
        json={"phone_number": "+27 11 999 0000"},
        headers=auth_headers(tokens),
    )
    assert res.status_code == 200
    assert res.json()["phone_number"] == "+27 11 999 0000"

    # Employee cannot deactivate self (no such endpoint exposed to them)
    forbidden = await client.patch(
        f"/api/v1/employees/{emp['id']}/status",
        json={"employment_status": "inactive"},
        headers=auth_headers(tokens),
    )
    assert forbidden.status_code == 403
