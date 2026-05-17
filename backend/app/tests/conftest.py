"""Pytest fixtures — uses ephemeral SQLite for isolated, fast unit tests.

Production runs on PostgreSQL; tests verify business logic only. We patch
PostgreSQL-specific column types (UUID, JSONB) on the SQLAlchemy metadata
so the schema is portable to SQLite for the test run.
"""
import asyncio
import os
import uuid

import pytest
import pytest_asyncio

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SYNC_DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "memory://")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_DEBUG", "false")

from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID  # noqa: E402
from sqlalchemy.types import JSON, CHAR, TypeDecorator  # noqa: E402


class _UUIDString(TypeDecorator):
    """Portable UUID column for SQLite (stored as CHAR(36))."""

    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value) if not isinstance(value, str) else value

    def process_result_value(self, value, dialect):
        return uuid.UUID(value) if value else None


# Import models so metadata is populated, then rewrite PG-specific column types.
from app.core.database import Base, AsyncSessionLocal, engine  # noqa: E402
import app.models  # noqa: F401,E402  (registers tables)

for table in Base.metadata.tables.values():
    for col in table.columns:
        if isinstance(col.type, PGUUID):
            col.type = _UUIDString()
        elif isinstance(col.type, JSONB):
            col.type = JSON()

from app.main import app  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def _reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def admin_tokens(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@test.com",
            "password": "Admin12345!",
            "first_name": "Test",
            "last_name": "Admin",
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


def auth_headers(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}
