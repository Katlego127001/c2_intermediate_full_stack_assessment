"""Job schemas."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.job import JobPriority, JobStatus


class JobBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    priority: JobPriority = JobPriority.MEDIUM
    due_date: datetime | None = None


class JobCreate(JobBase):
    # Keep create permissive for tests and callers: most fields are optional
    # (description/due_date/assigned_employee_id/status). Validation at the
    # service layer ensures business rules (e.g. assigned employee exists).
    description: str | None = None
    # allow callers to omit due_date and status; default status to PENDING in service
    due_date: datetime | None = None
    assigned_employee_id: uuid.UUID | None = None
    status: JobStatus | None = None


class JobUpdate(BaseModel):
    """Admin can update everything."""
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    priority: JobPriority | None = None
    status: JobStatus | None = None
    due_date: datetime | None = None
    assigned_employee_id: uuid.UUID | None = None


class JobStatusUpdate(BaseModel):
    """Employee-allowed update — status only."""
    status: JobStatus
    comment: str | None = Field(default=None, max_length=1024)


class AssigneeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    full_name: str
    department: str | None = None


class JobOut(JobBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: JobStatus
    assigned_employee_id: uuid.UUID | None = None
    assignee: AssigneeSummary | None = None
    last_status_comment: str | None = None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
