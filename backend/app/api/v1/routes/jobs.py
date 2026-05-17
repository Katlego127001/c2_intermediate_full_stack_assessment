"""Job management endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user, require_admin
from app.api.v1.dependencies.pagination import PaginationParams, pagination_params
from app.core.database import get_db
from app.models.job import JobPriority, JobStatus
from app.models.user import User, UserRole
from app.repositories.job import JobRepository
from app.repositories.activity import ActivityRepository
from app.schemas.common import Message, Page
from app.schemas.job import (
    AssigneeSummary,
    JobCreate,
    JobOut,
    JobStatusUpdate,
    JobUpdate,
)
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _to_out(job) -> JobOut:
    assignee = None
    if job.assignee:
        assignee = AssigneeSummary(
            id=job.assignee.id,
            full_name=f"{job.assignee.first_name} {job.assignee.last_name}",
            department=job.assignee.department,
        )
    return JobOut(
        id=job.id,
        title=job.title,
        description=job.description,
        priority=job.priority,
        status=job.status,
        due_date=job.due_date,
        assigned_employee_id=job.assigned_employee_id,
        assignee=assignee,
        created_by=job.created_by,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("", response_model=Page[JobOut])
async def list_jobs(
    q: str | None = None,
    status_: JobStatus | None = Query(None, alias="status"),
    priority: JobPriority | None = None,
    mine: bool = Query(False, description="If true, returns only jobs assigned to current user"),
    assignee_id: uuid.UUID | None = None,
    pagination: PaginationParams = Depends(pagination_params),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Page[JobOut]:
    repo = JobRepository(session)
    # Employees: always restricted to their own jobs.
    effective_assignee = assignee_id
    if user.role == UserRole.EMPLOYEE:
        if not user.employee:
            return Page[JobOut](items=[], total=0, page=pagination.page, size=pagination.size, pages=1)
        effective_assignee = user.employee.id
    elif mine and user.employee:
        effective_assignee = user.employee.id

    items, total = await repo.search(
        q=q,
        status=status_,
        priority=priority,
        assignee_id=effective_assignee,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    # fetch latest status comment for each job (optimize later if needed)
    act_repo = ActivityRepository(session)
    out_items = []
    for j in items:
        last = await act_repo.latest_for_entity("job", str(j.id), action="update_job_status")
        jo = _to_out(j)
        if last and getattr(last, "metadata_", None):
            try:
                jo.last_status_comment = last.metadata_.get("comment")
            except Exception:
                jo.last_status_comment = None
        else:
            jo.last_status_comment = None
        out_items.append(jo)
    return Page[JobOut](
        items=out_items,
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=max(1, (total + pagination.size - 1) // pagination.size),
    )


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    session: AsyncSession = Depends(get_db),
    actor: User = Depends(require_admin),
) -> JobOut:
    service = JobService(session)
    job = await service.create(payload, actor)
    return _to_out(job)


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> JobOut:
    repo = JobRepository(session)
    job = await repo.get_full(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if user.role == UserRole.EMPLOYEE:
        if not user.employee or job.assigned_employee_id != user.employee.id:
            raise HTTPException(status_code=403, detail="Forbidden")
    act_repo = ActivityRepository(session)
    last = await act_repo.latest_for_entity("job", str(job.id), action="update_job_status")
    jo = _to_out(job)
    if last and getattr(last, "metadata_", None):
        try:
            jo.last_status_comment = last.metadata_.get("comment")
        except Exception:
            jo.last_status_comment = None
    else:
        jo.last_status_comment = None
    return jo


@router.put("/{job_id}", response_model=JobOut)
async def update_job(
    job_id: uuid.UUID,
    payload: JobUpdate,
    session: AsyncSession = Depends(get_db),
    actor: User = Depends(require_admin),
) -> JobOut:
    service = JobService(session)
    job = await service.update_admin(job_id, payload, actor)
    return _to_out(job)


@router.patch("/{job_id}/status", response_model=JobOut)
async def update_job_status(
    job_id: uuid.UUID,
    payload: JobStatusUpdate,
    session: AsyncSession = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> JobOut:
    """Both admins and the assigned employee may update status. Optionally
    accepts a `comment` describing the change (e.g., progress note, rationale).
    """
    service = JobService(session)
    job = await service.update_status(job_id, payload.status, actor, payload.comment)
    return _to_out(job)


@router.delete("/{job_id}", response_model=Message)
async def delete_job(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    actor: User = Depends(require_admin),
) -> Message:
    service = JobService(session)
    await service.soft_delete(job_id, actor)
    return Message(message="Job deleted")
