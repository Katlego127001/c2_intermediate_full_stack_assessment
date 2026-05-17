"""Job management business logic."""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus
from app.models.user import User, UserRole
from app.repositories.employee import EmployeeRepository
from app.models.employee import EmploymentStatus
from app.repositories.job import JobRepository
from app.schemas.job import JobCreate, JobUpdate
from app.services.activity_service import ActivityService
from app.websockets.manager import ws_manager


class JobService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = JobRepository(session)
        self.employees = EmployeeRepository(session)
        self.activity = ActivityService(session)

    async def _ensure_assignee_exists(self, employee_id):
        if employee_id is None:
            return
        emp = await self.employees.get(employee_id)
        if not emp:
            raise HTTPException(status_code=400, detail="Assigned employee does not exist")
        if emp.employment_status != EmploymentStatus.ACTIVE:
            # If employee is not active, don't allow assignment
            raise HTTPException(status_code=400, detail="Assigned employee is not active")

    async def create(self, data: JobCreate, actor: User) -> Job:
        await self._ensure_assignee_exists(data.assigned_employee_id)
        job = Job(
            title=data.title,
            description=data.description,
            priority=data.priority,
            status=data.status,
            due_date=data.due_date,
            assigned_employee_id=data.assigned_employee_id,
            created_by=actor.id,
        )
        self.session.add(job)
        await self.session.flush()
        await self.activity.log(
            actor_id=actor.id,
            action="create_job",
            entity_type="job",
            entity_id=str(job.id),
            metadata={"title": job.title},
        )
        await self.session.commit()
        full = await self.repo.get_full(job.id)
        # Notify assignee in real-time
        if full and full.assigned_employee_id:
            await ws_manager.notify_employee(
                full.assigned_employee_id,
                {"type": "job.assigned", "job_id": str(full.id), "title": full.title},
            )
        return full  # type: ignore[return-value]

    async def update_admin(self, job_id, data: JobUpdate, actor: User) -> Job:
        job = await self.repo.get_full(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        await self._ensure_assignee_exists(data.assigned_employee_id)

        prev_assignee = job.assigned_employee_id
        for field in ("title", "description", "priority", "status", "due_date", "assigned_employee_id"):
            val = getattr(data, field)
            if val is not None:
                setattr(job, field, val)
        await self.activity.log(
            actor_id=actor.id,
            action="update_job",
            entity_type="job",
            entity_id=str(job.id),
            metadata=data.model_dump(exclude_none=True, mode="json"),
        )
        await self.session.commit()
        full = await self.repo.get_full(job.id)
        if full and full.assigned_employee_id and full.assigned_employee_id != prev_assignee:
            await ws_manager.notify_employee(
                full.assigned_employee_id,
                {"type": "job.assigned", "job_id": str(full.id), "title": full.title},
            )
        return full  # type: ignore[return-value]

    async def update_status(self, job_id, new_status: JobStatus, actor: User, comment: str | None = None) -> Job:
        job = await self.repo.get_full(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        # Employees can only update jobs assigned to them
        if actor.role == UserRole.EMPLOYEE:
            if not actor.employee or job.assigned_employee_id != actor.employee.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update status of jobs assigned to you",
                )
        job.status = new_status
        metadata = {"status": new_status.value}
        if comment:
            metadata["comment"] = comment
        await self.activity.log(
            actor_id=actor.id,
            action="update_job_status",
            entity_type="job",
            entity_id=str(job.id),
            metadata=metadata,
        )
        await self.session.commit()
        full = await self.repo.get_full(job.id)
        # Notify assignee about status change (include comment if provided)
        if full and full.assigned_employee_id:
            await ws_manager.notify_employee(
                full.assigned_employee_id,
                {
                    "type": "job.status_changed",
                    "job_id": str(full.id),
                    "status": new_status.value,
                    "comment": comment,
                },
            )
        return full  # type: ignore[return-value]

    async def soft_delete(self, job_id, actor: User) -> None:
        job = await self.repo.get_full(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        job.is_deleted = True
        job.deleted_at = datetime.now(timezone.utc)
        await self.activity.log(
            actor_id=actor.id, action="delete_job", entity_type="job", entity_id=str(job.id)
        )
        await self.session.commit()
