from sqlalchemy import func as sa_func
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.models.employee import Employee
from app.models.job import Job, JobPriority, JobStatus
from app.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    model = Job

    def _base_stmt(self):
        return select(Job).options(selectinload(Job.assignee))

    async def get_full(self, job_id) -> Job | None:
        stmt = self._base_stmt().where(Job.id == job_id, Job.is_deleted.is_(False))
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def search(
        self,
        *,
        q: str | None = None,
        status: JobStatus | None = None,
        priority: JobPriority | None = None,
        assignee_id=None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Job], int]:
        where = [Job.is_deleted.is_(False)]
        if q:
            like = f"%{q.lower()}%"
            where.append(or_(Job.title.ilike(like), Job.description.ilike(like)))
        if status:
            where.append(Job.status == status)
        if priority:
            where.append(Job.priority == priority)
        if assignee_id:
            where.append(Job.assigned_employee_id == assignee_id)

        stmt = self._base_stmt()
        for w in where:
            stmt = stmt.where(w)

        count_stmt = select(sa_func.count()).select_from(Job)
        for w in where:
            count_stmt = count_stmt.where(w)
        total = int((await self.session.execute(count_stmt)).scalar_one())

        stmt = stmt.order_by(Job.created_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().unique().all()), total

    async def count_by_status(self, *, assignee_id=None) -> dict[JobStatus, int]:
        stmt = select(Job.status, sa_func.count()).where(Job.is_deleted.is_(False))
        if assignee_id:
            stmt = stmt.where(Job.assigned_employee_id == assignee_id)
        stmt = stmt.group_by(Job.status)
        res = await self.session.execute(stmt)
        return {row[0]: int(row[1]) for row in res.all()}

    async def workload_by_employee(self) -> list[tuple[Employee, dict]]:
        stmt = (
            select(
                Employee,
                Job.status,
                sa_func.count(Job.id),
            )
            .join(Job, Job.assigned_employee_id == Employee.id, isouter=True)
            .where(or_(Job.is_deleted.is_(False), Job.id.is_(None)))
            .group_by(Employee.id, Job.status)
        )
        res = await self.session.execute(stmt)
        agg: dict = {}
        for emp, status, count in res.all():
            bucket = agg.setdefault(emp.id, {"employee": emp, "counts": {}})
            if status is not None:
                bucket["counts"][status] = int(count)
        return list(agg.values())

    async def upcoming_for(self, employee_id, *, limit: int = 5) -> list[Job]:
        stmt = (
            self._base_stmt()
            .where(
                Job.assigned_employee_id == employee_id,
                Job.is_deleted.is_(False),
                Job.status != JobStatus.COMPLETED,
                Job.due_date.is_not(None),
            )
            .order_by(Job.due_date.asc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def list_for_assignee(self, employee_id, *, status: JobStatus | None = None) -> list[Job]:
        """Return all jobs assigned to an employee, optionally filtered by status."""
        stmt = self._base_stmt().where(
            Job.assigned_employee_id == employee_id,
            Job.is_deleted.is_(False),
        )
        if status is not None:
            stmt = stmt.where(Job.status == status)
        stmt = stmt.order_by(Job.created_at.desc())
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
