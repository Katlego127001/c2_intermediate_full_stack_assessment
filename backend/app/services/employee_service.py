"""Employee management business logic (admin operations)."""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.employee import Employee, EmploymentStatus
from app.models.user import User, UserRole
from app.repositories.employee import EmployeeRepository
from app.repositories.user import UserRepository
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.services.activity_service import ActivityService


class EmployeeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = EmployeeRepository(session)
        self.users = UserRepository(session)
        self.activity = ActivityService(session)

    async def create(self, data: EmployeeCreate, actor: User) -> Employee:
        if await self.users.get_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
            )

        user = User(
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            role=data.role,
            is_active=data.employment_status == EmploymentStatus.ACTIVE,
        )
        emp = Employee(
            first_name=data.first_name,
            last_name=data.last_name,
            phone_number=data.phone_number,
            department=data.department,
            employment_status=data.employment_status,
        )
        user.employee = emp
        self.session.add(user)
        await self.session.flush()
        await self.activity.log(
            actor_id=actor.id,
            action="create_employee",
            entity_type="employee",
            entity_id=str(emp.id),
            metadata={"email": user.email, "role": user.role.value},
        )
        await self.session.commit()
        return await self.repo.get_with_user(emp.id)  # type: ignore[return-value]

    async def update(self, employee_id, data: EmployeeUpdate, actor: User) -> Employee:
        emp = await self.repo.get_with_user(employee_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        changes: dict = {}
        for field in ("first_name", "last_name", "phone_number", "department", "employment_status"):
            val = getattr(data, field)
            if val is not None:
                changes[field] = val
                setattr(emp, field, val)
        if data.role is not None:
            emp.user.role = data.role
            changes["role"] = data.role.value
        if data.employment_status is not None:
            emp.user.is_active = data.employment_status == EmploymentStatus.ACTIVE

        await self.activity.log(
            actor_id=actor.id,
            action="update_employee",
            entity_type="employee",
            entity_id=str(emp.id),
            metadata={k: (v.value if hasattr(v, "value") else v) for k, v in changes.items()},
        )
        await self.session.commit()
        return await self.repo.get_with_user(emp.id)  # type: ignore[return-value]

    async def set_status(self, employee_id, new_status: EmploymentStatus, actor: User) -> Employee:
        emp = await self.repo.get_with_user(employee_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        emp.employment_status = new_status
        emp.user.is_active = new_status == EmploymentStatus.ACTIVE
        await self.activity.log(
            actor_id=actor.id,
            action="set_employee_status",
            entity_type="employee",
            entity_id=str(emp.id),
            metadata={"employment_status": new_status.value},
        )
        await self.session.commit()
        return await self.repo.get_with_user(emp.id)  # type: ignore[return-value]

    async def update_self_phone(self, user: User, phone: str | None) -> Employee:
        emp = await self.repo.get_by_user_id(user.id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee profile not found")
        # Validate format (allow spaces/dashes/parens) and store the original
        metadata = None
        if phone is not None:
            import re

            s = re.sub(r"[\s\-()]+", "", phone)
            if not re.fullmatch(r"\+?\d{7,15}", s):
                raise HTTPException(status_code=400, detail="Invalid phone number format")
            # store original formatting in the employee record but keep a
            # normalized version in the activity metadata
            metadata = {"phone_number": s}
        emp.phone_number = phone
        await self.activity.log(
            actor_id=user.id,
            action="update_self_phone",
            entity_type="employee",
            entity_id=str(emp.id),
            metadata=metadata,
        )
        await self.session.commit()
        return await self.repo.get_with_user(emp.id)  # type: ignore[return-value]
