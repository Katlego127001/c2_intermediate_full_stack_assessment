from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.models.employee import Employee, EmploymentStatus
from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class EmployeeRepository(BaseRepository[Employee]):
    model = Employee

    def _base_stmt(self):
        return select(Employee).options(selectinload(Employee.user))

    async def get_with_user(self, employee_id) -> Employee | None:
        stmt = self._base_stmt().where(Employee.id == employee_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_user_id(self, user_id) -> Employee | None:
        stmt = self._base_stmt().where(Employee.user_id == user_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def search(
        self,
        *,
        q: str | None = None,
        department: str | None = None,
        status: EmploymentStatus | None = None,
        role: UserRole | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Employee], int]:
        """Search/filter employees.

        Spec: search by name or department; filter by role or status.
        """
        stmt = self._base_stmt().join(User, Employee.user_id == User.id)
        where = [User.is_deleted.is_(False)]
        if q:
            like = f"%{q.lower()}%"
            where.append(
                or_(
                    Employee.first_name.ilike(like),
                    Employee.last_name.ilike(like),
                    User.email.ilike(like),
                    Employee.department.ilike(like),
                )
            )
        if department:
            where.append(Employee.department == department)
        if status:
            where.append(Employee.employment_status == status)
        if role:
            where.append(User.role == role)

        for w in where:
            stmt = stmt.where(w)

        from sqlalchemy import func as sa_func

        count_stmt = select(sa_func.count()).select_from(Employee).join(
            User, Employee.user_id == User.id
        )
        for w in where:
            count_stmt = count_stmt.where(w)
        total = int((await self.session.execute(count_stmt)).scalar_one())

        stmt = stmt.order_by(Employee.created_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().unique().all()), total
