"""Dashboard aggregation service."""
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import ActivityLog
from app.models.employee import Employee, EmploymentStatus
from app.models.job import Job, JobStatus
from app.models.user import User
from app.repositories.job import JobRepository
from app.schemas.dashboard import (
    AdminDashboard,
    EmployeeCounts,
    EmployeeDashboard,
    JobCounts,
    RecentActivity,
    UpcomingDue,
    AlertItem,
    WorkloadItem,
)


class DashboardService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.jobs_repo = JobRepository(session)

    async def admin(self) -> AdminDashboard:
        # Job counts
        by_status = await self.jobs_repo.count_by_status()
        total_jobs = sum(by_status.values())
        jobs = JobCounts(
            total=total_jobs,
            pending=by_status.get(JobStatus.PENDING, 0),
            in_progress=by_status.get(JobStatus.IN_PROGRESS, 0),
            completed=by_status.get(JobStatus.COMPLETED, 0),
        )

        # Employee counts
        emp_total = int(
            (await self.session.execute(select(sa_func.count(Employee.id)))).scalar_one()
        )
        emp_active = int(
            (
                await self.session.execute(
                    select(sa_func.count(Employee.id)).where(
                        Employee.employment_status == EmploymentStatus.ACTIVE
                    )
                )
            ).scalar_one()
        )
        employees = EmployeeCounts(
            total=emp_total, active=emp_active, inactive=emp_total - emp_active
        )

        # Workload
        workload_rows = await self.jobs_repo.workload_by_employee()
        workload: list[WorkloadItem] = []
        for row in workload_rows:
            emp: Employee = row["employee"]
            counts = row["counts"]
            workload.append(
                WorkloadItem(
                    employee_id=emp.id,
                    full_name=f"{emp.first_name} {emp.last_name}",
                    department=emp.department,
                    pending=counts.get(JobStatus.PENDING, 0),
                    in_progress=counts.get(JobStatus.IN_PROGRESS, 0),
                    completed=counts.get(JobStatus.COMPLETED, 0),
                    total=sum(counts.values()),
                )
            )
        workload.sort(key=lambda x: x.total, reverse=True)

        # Recent activity
        stmt = (
            select(ActivityLog, User)
            .join(User, User.id == ActivityLog.actor_id, isouter=True)
            .order_by(ActivityLog.created_at.desc())
            .limit(10)
        )
        rows = (await self.session.execute(stmt)).all()
        recent = [
            RecentActivity(
                id=a.id,
                actor_email=(u.email if u else None),
                action=a.action,
                entity_type=a.entity_type,
                entity_id=a.entity_id,
                created_at=a.created_at,
            )
            for a, u in rows
        ]

        return AdminDashboard(
            jobs=jobs, employees=employees, workload=workload, recent_activity=recent
        )

    async def employee(self, employee: Employee) -> EmployeeDashboard:
        by_status = await self.jobs_repo.count_by_status(assignee_id=employee.id)
        total = sum(by_status.values())
        jobs = JobCounts(
            total=total,
            pending=by_status.get(JobStatus.PENDING, 0),
            in_progress=by_status.get(JobStatus.IN_PROGRESS, 0),
            completed=by_status.get(JobStatus.COMPLETED, 0),
        )
        upcoming_jobs = await self.jobs_repo.upcoming_for(employee.id, limit=5)
        upcoming = [
            UpcomingDue(
                id=j.id,
                title=j.title,
                due_date=j.due_date,
                priority=j.priority.value,
                status=j.status.value,
            )
            for j in upcoming_jobs
        ]
        # Alerts: pending jobs that are overdue or due within 3 days
        from datetime import datetime, timezone, timedelta

        alerts: list[AlertItem] = []
        now = datetime.now(timezone.utc)
        three_days = now + timedelta(days=3)
        pending_jobs = await self.jobs_repo.list_for_assignee(employee.id, status=JobStatus.PENDING)
        for j in pending_jobs:
            if j.due_date is None:
                continue
            if j.due_date < now:
                msg = "Overdue"
            elif j.due_date <= three_days:
                msg = "Due soon"
            else:
                continue
            alerts.append(
                AlertItem(
                    id=j.id,
                    title=j.title,
                    due_date=j.due_date,
                    priority=j.priority.value,
                    status=j.status.value,
                    message=msg,
                )
            )
        return EmployeeDashboard(
            profile={
                "id": str(employee.id),
                "full_name": f"{employee.first_name} {employee.last_name}",
                "department": employee.department,
                "email": employee.user.email if employee.user else None,
            },
            jobs=jobs,
            upcoming=upcoming,
            alerts=alerts,
        )
