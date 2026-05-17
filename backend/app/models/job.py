"""Job model — units of work assigned to employees."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class JobPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Job(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("ix_jobs_status_priority", "status", "priority"),
        Index("ix_jobs_due_date", "due_date"),
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Use values_callable so DB-bound values match migration-created labels
    # (lowercase strings) instead of enum member names.
    priority: Mapped[JobPriority] = mapped_column(
        Enum(
            JobPriority,
            name="job_priority",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=JobPriority.MEDIUM,
        nullable=False,
        index=True,
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(
            JobStatus,
            name="job_status",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=JobStatus.PENDING,
        nullable=False,
        index=True,
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    assigned_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    assignee = relationship(
        "Employee", back_populates="assigned_jobs", foreign_keys=[assigned_employee_id]
    )
    creator = relationship("User", foreign_keys=[created_by])
