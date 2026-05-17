"""Employee profile, 1:1 with User."""
import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class EmploymentStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Employee(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "employees"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    # Ensure the DB-bound enum values match the migration-created labels
    # (lowercase strings) by using values_callable.
    employment_status: Mapped[EmploymentStatus] = mapped_column(
        Enum(
            EmploymentStatus,
            name="employment_status",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=EmploymentStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    user = relationship("User", back_populates="employee")
    assigned_jobs = relationship(
        "Job", back_populates="assignee", foreign_keys="Job.assigned_employee_id"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
