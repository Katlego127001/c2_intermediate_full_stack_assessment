"""Dashboard response schemas."""
import uuid
from datetime import datetime

from pydantic import BaseModel


class JobCounts(BaseModel):
    total: int
    pending: int
    in_progress: int
    completed: int


class EmployeeCounts(BaseModel):
    total: int
    active: int
    inactive: int


class WorkloadItem(BaseModel):
    employee_id: uuid.UUID
    full_name: str
    department: str | None = None
    pending: int
    in_progress: int
    completed: int
    total: int


class RecentActivity(BaseModel):
    id: uuid.UUID
    actor_email: str | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    created_at: datetime


class AdminDashboard(BaseModel):
    jobs: JobCounts
    employees: EmployeeCounts
    workload: list[WorkloadItem]
    recent_activity: list[RecentActivity]


class UpcomingDue(BaseModel):
    id: uuid.UUID
    title: str
    due_date: datetime | None
    priority: str
    status: str


class AlertItem(BaseModel):
    id: uuid.UUID
    title: str
    due_date: datetime | None
    priority: str
    status: str
    message: str


class EmployeeDashboard(BaseModel):
    profile: dict
    jobs: JobCounts
    upcoming: list[UpcomingDue]
    alerts: list[AlertItem] = []
