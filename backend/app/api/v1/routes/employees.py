"""Employee management endpoints."""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import (
    get_current_user,
    require_admin,
)
from app.api.v1.dependencies.pagination import PaginationParams, pagination_params
from app.core.database import get_db
from app.models.employee import EmploymentStatus
from app.models.user import User, UserRole
from app.repositories.employee import EmployeeRepository
from app.schemas.common import Page
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeOut,
    EmployeeSelfUpdate,
    EmployeeStatusUpdate,
    EmployeeUpdate,
)
from app.services.employee_service import EmployeeService

router = APIRouter(prefix="/employees", tags=["employees"])


def _to_out(emp) -> EmployeeOut:
    return EmployeeOut(
        id=emp.id,
        user_id=emp.user_id,
        first_name=emp.first_name,
        last_name=emp.last_name,
        phone_number=emp.phone_number,
        department=emp.department,
        email=emp.user.email,
        role=emp.user.role,
        employment_status=emp.employment_status,
        is_active=emp.user.is_active,
        created_at=emp.created_at,
        updated_at=emp.updated_at,
        full_name=f"{emp.first_name} {emp.last_name}",
    )


@router.get("", response_model=Page[EmployeeOut])
async def list_employees(
    q: str | None = Query(None, description="Search by name, email or department"),
    department: str | None = None,
    status_: EmploymentStatus | None = Query(None, alias="status"),
    role: UserRole | None = Query(None, description="Filter by role (admin/employee)"),
    pagination: PaginationParams = Depends(pagination_params),
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> Page[EmployeeOut]:
    repo = EmployeeRepository(session)
    items, total = await repo.search(
        q=q,
        department=department,
        status=status_,
        role=role,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return Page[EmployeeOut](
        items=[_to_out(e) for e in items],
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=max(1, (total + pagination.size - 1) // pagination.size),
    )


@router.post("", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
async def create_employee(
    payload: EmployeeCreate,
    session: AsyncSession = Depends(get_db),
    actor: User = Depends(require_admin),
) -> EmployeeOut:
    service = EmployeeService(session)
    emp = await service.create(payload, actor)
    return _to_out(emp)


@router.get("/me", response_model=EmployeeOut)
async def get_my_profile(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmployeeOut:
    repo = EmployeeRepository(session)
    emp = await repo.get_by_user_id(user.id)
    if not emp:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="No employee profile")
    return _to_out(emp)


@router.patch("/me", response_model=EmployeeOut)
async def update_my_profile(
    payload: EmployeeSelfUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmployeeOut:
    service = EmployeeService(session)
    emp = await service.update_self_phone(user, payload.phone_number)
    return _to_out(emp)


@router.get("/{employee_id}", response_model=EmployeeOut)
async def get_employee(
    employee_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> EmployeeOut:
    repo = EmployeeRepository(session)
    emp = await repo.get_with_user(employee_id)
    if not emp:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Employee not found")
    return _to_out(emp)


@router.put("/{employee_id}", response_model=EmployeeOut)
async def update_employee(
    employee_id: uuid.UUID,
    payload: EmployeeUpdate,
    session: AsyncSession = Depends(get_db),
    actor: User = Depends(require_admin),
) -> EmployeeOut:
    service = EmployeeService(session)
    emp = await service.update(employee_id, payload, actor)
    return _to_out(emp)


@router.patch("/{employee_id}/status", response_model=EmployeeOut)
async def set_employee_status(
    employee_id: uuid.UUID,
    payload: EmployeeStatusUpdate,
    session: AsyncSession = Depends(get_db),
    actor: User = Depends(require_admin),
) -> EmployeeOut:
    service = EmployeeService(session)
    emp = await service.set_status(employee_id, payload.employment_status, actor)
    return _to_out(emp)
