"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # 1. Inspect the database schema to see what objects already exist
    bind = op.get_bind()
    inspect = sa.inspect(bind)
    existing_enums = [e['name'] for e in inspect.get_enums()]

    # 2. Define the target PostgreSQL ENUM types explicitly
    enum_user_role = postgresql.ENUM("admin", "employee", name="user_role")
    enum_employment_status = postgresql.ENUM("active", "inactive", name="employment_status")
    enum_job_priority = postgresql.ENUM("low", "medium", "high", "critical", name="job_priority")
    enum_job_status = postgresql.ENUM("pending", "in_progress", "completed", name="job_status")

    # 3. Only create the types if they are completely missing from the DB
    if "user_role" not in existing_enums:
        enum_user_role.create(bind)
    if "employment_status" not in existing_enums:
        enum_employment_status.create(bind)
    if "job_priority" not in existing_enums:
        enum_job_priority.create(bind)
    if "job_status" not in existing_enums:
        enum_job_status.create(bind)

    # 4. Create your tables. 
    # CRITICAL: Pass create_type=False to stop SQLAlchemy from auto-generating types implicitly.
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", postgresql.ENUM("admin", "employee", name="user_role", create_type=False), 
                  nullable=False, server_default="employee"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_is_active", "users", ["is_active"])
    op.create_index("ix_users_is_deleted", "users", ["is_deleted"])

    op.create_table(
        "employees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("first_name", sa.String(80), nullable=False),
        sa.Column("last_name", sa.String(80), nullable=False),
        sa.Column("phone_number", sa.String(40), nullable=True),
        sa.Column("department", sa.String(120), nullable=True),
        sa.Column("employment_status", postgresql.ENUM("active", "inactive", name="employment_status", create_type=False), 
                  nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_employees_department", "employees", ["department"])
    op.create_index("ix_employees_employment_status", "employees", ["employment_status"])

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("priority", postgresql.ENUM("low", "medium", "high", "critical", name="job_priority", create_type=False), 
                  nullable=False, server_default="medium"),
        sa.Column("status", postgresql.ENUM("pending", "in_progress", "completed", name="job_status", create_type=False), 
                  nullable=False, server_default="pending"),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_employee_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("employees.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("is_deleted", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_priority", "jobs", ["priority"])
    op.create_index("ix_jobs_assigned_employee_id", "jobs", ["assigned_employee_id"])
    op.create_index("ix_jobs_created_by", "jobs", ["created_by"])
    op.create_index("ix_jobs_status_priority", "jobs", ["status", "priority"])
    op.create_index("ix_jobs_due_date", "jobs", ["due_date"])
    op.create_index("ix_jobs_is_deleted", "jobs", ["is_deleted"])

    op.create_table(
        "activity_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", sa.String(80), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_activity_logs_actor_id", "activity_logs", ["actor_id"])
    op.create_index("ix_activity_logs_action", "activity_logs", ["action"])
    op.create_index("ix_activity_logs_entity_type", "activity_logs", ["entity_type"])
    op.create_index("ix_activity_logs_entity_id", "activity_logs", ["entity_id"])


def downgrade() -> None:
    op.drop_table("activity_logs")
    op.drop_table("jobs")
    op.drop_table("employees")
    op.drop_table("users")
    
    # Use postgresql.ENUM for explicit dropping behavior
    bind = op.get_bind()
    postgresql.ENUM(name="job_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="job_priority").drop(bind, checkfirst=True)
    postgresql.ENUM(name="employment_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="user_role").drop(bind, checkfirst=True)