"""Idempotent seed script: bootstraps admin + sample employees + jobs.

Run with:  python -m app.utils.seed
"""
import asyncio
import enum
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from sqlalchemy import create_engine as _create_engine
from app.core.database import Base as _Base
from alembic import command as _alembic_command
from alembic.config import Config as _AlembicConfig
from app.core.logging import configure_logging, get_logger
from app.core.security import hash_password
from app.models.employee import Employee, EmploymentStatus
from app.models.job import Job, JobPriority, JobStatus
from app.models.user import User, UserRole

configure_logging()
log = get_logger("seed")


SAMPLE_EMPLOYEES = [
    ("alice@jobtracker.com", "Password123!", "Alice", "Anderson", "Engineering", "+27 11 555 0001"),
    ("bob@jobtracker.com", "Password123!", "Bob", "Brown", "Engineering", "+27 11 555 0002"),
    ("carol@jobtracker.com", "Password123!", "Carol", "Clark", "Design", "+27 11 555 0003"),
    ("dan@jobtracker.com", "Password123!", "Dan", "Davis", "Operations", "+27 11 555 0004"),
]


SAMPLE_JOBS = [
    ("Set up CI pipeline", "Configure GitHub Actions for tests & build", JobPriority.HIGH, JobStatus.IN_PROGRESS, 3),
    ("Design login page", "Refresh visual style for auth screens", JobPriority.MEDIUM, JobStatus.PENDING, 7),
    ("Fix prod database backup", "Backup cron failed last night", JobPriority.CRITICAL, JobStatus.PENDING, 1),
    ("Write onboarding docs", "Internal Confluence page for new hires", JobPriority.LOW, JobStatus.COMPLETED, -2),
    ("Audit IAM permissions", "Quarterly access review", JobPriority.HIGH, JobStatus.PENDING, 10),
    ("Optimize search query", "Slow query in jobs/list endpoint", JobPriority.MEDIUM, JobStatus.IN_PROGRESS, 5),
]


async def _get_or_create_user(session, *, email, password, role, first, last, dept, phone, status):
    res = await session.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    if user:
        return user
    # If caller passed a Python Enum, store its underlying value (e.g. 'admin')
    # to match the PostgreSQL ENUM values created by the migration.
    role_value = role.value if isinstance(role, enum.Enum) else role
    user = User(
        email=email,
        password_hash=hash_password(password),
        role=role_value,
        is_active=status == EmploymentStatus.ACTIVE,
    )
    user.employee = Employee(
        first_name=first,
        last_name=last,
        department=dept,
        phone_number=phone,
        employment_status=status,
    )
    session.add(user)
    # Debug: log the incoming role, computed role_value, and types so we can
    # verify what SQLAlchemy will try to bind to the DB for the enum column.
    try:
        log.info(
            "seed.debug.pre_flush",
            email=email,
            passed_role=repr(role),
            passed_role_type=str(type(role)),
            role_value=repr(role_value),
        )
    except Exception:
        # keep seeding tolerant of logging failures
        pass
    await session.flush()
    try:
        log.info(
            "seed.debug.post_flush",
            email=email,
            user_role=repr(user.role),
            user_role_type=str(type(user.role)),
        )
    except Exception:
        pass
    # safe final created log: role_value is a string here (or whatever was passed)
    log.info("seed.user.created", email=email, role=role_value)
    return user


async def main():
    # Ensure alembic migrations have run in this process before attempting
    # to open an AsyncSession and run ORM queries. Running alembic here makes
    # the seeder resilient to entrypoint ordering/race issues where a
    # previous alembic invocation may not have completed the DDL we expect.
    try:
        cfg = _AlembicConfig("alembic.ini")
        # run in thread to avoid blocking the event loop
        import asyncio as _asyncio

        await _asyncio.to_thread(_alembic_command.upgrade, cfg, "head")
        log.info("seed.alembic.upgrade", status="ok")
    except Exception as exc:  # pragma: no cover - operational
        log.exception("seed.alembic.failed", error=repr(exc))

    # Quick check: if alembic didn't create the tables for some reason
    # (we've seen alembic_version present but application tables missing),
    # attempt to create them via SQLAlchemy's metadata.create_all as a
    # last-resort recovery. This uses the synchronous engine and runs in
    # a thread to avoid blocking the async loop.
    try:
        def _ensure_tables():
            engine = _create_engine(settings.SYNC_DATABASE_URL)
            # create_all is idempotent and will create any missing tables/types
            _Base.metadata.create_all(engine)

        await _asyncio.to_thread(_ensure_tables)
        log.info("seed.metadata.create_all", status="ok")
    except Exception as exc:  # pragma: no cover - operational
        log.exception("seed.metadata.create_all.failed", error=repr(exc))

    async with AsyncSessionLocal() as session:
        # Poll for the `users` table as a last-resort guard in case migrations
        # completed but the DB is still finalizing. This is defensive only.
        import asyncio as _asyncio

        max_wait = 60  # seconds
        interval = 1
        waited = 0
        while waited < max_wait:
            try:
                res = await session.execute("SELECT to_regclass('public.users')")
                val = res.scalar_one_or_none()
                if val:
                    break
            except Exception:
                # swallow transient DB errors and retry until timeout
                pass
            await _asyncio.sleep(interval)
            waited += interval
        if waited >= max_wait:
            log.warning("seed.timeout.waiting_for_tables", waited=waited)
        admin = await _get_or_create_user(
            session,
            email=settings.FIRST_ADMIN_EMAIL,
            password=settings.FIRST_ADMIN_PASSWORD,
            role=UserRole.ADMIN,
            first=settings.FIRST_ADMIN_FIRST_NAME,
            last=settings.FIRST_ADMIN_LAST_NAME,
            dept="Administration",
            phone=None,
            status=EmploymentStatus.ACTIVE,
        )

        employees = []
        for email, pw, first, last, dept, phone in SAMPLE_EMPLOYEES:
            u = await _get_or_create_user(
                session,
                email=email, password=pw, role=UserRole.EMPLOYEE,
                first=first, last=last, dept=dept, phone=phone,
                status=EmploymentStatus.ACTIVE,
            )
            employees.append(u)
        await session.flush()

        # Re-fetch with employee relation
        from sqlalchemy.orm import selectinload
        res = await session.execute(
            select(User).where(User.email.in_([e[0] for e in SAMPLE_EMPLOYEES]))
            .options(selectinload(User.employee))
        )
        emp_users = list(res.scalars().all())

        # Seed jobs if none exist
        existing_jobs = (await session.execute(select(Job))).scalars().first()
        if not existing_jobs:
            now = datetime.now(timezone.utc)
            for i, (title, desc, prio, status_, due_days) in enumerate(SAMPLE_JOBS):
                assignee = emp_users[i % len(emp_users)].employee
                job = Job(
                    title=title,
                    description=desc,
                    priority=prio,
                    status=status_,
                    due_date=now + timedelta(days=due_days),
                    assigned_employee_id=assignee.id,
                    created_by=admin.id,
                )
                session.add(job)
            log.info("seed.jobs.created", count=len(SAMPLE_JOBS))

        await session.commit()
        log.info("seed.complete")


if __name__ == "__main__":
    asyncio.run(main())
