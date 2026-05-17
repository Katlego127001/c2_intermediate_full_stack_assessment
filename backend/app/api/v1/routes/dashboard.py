"""Dashboard endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user, require_admin
from app.core.database import get_db
from app.models.user import User
from app.repositories.employee import EmployeeRepository
from app.schemas.dashboard import AdminDashboard, EmployeeDashboard
from app.services.dashboard_service import DashboardService
import uuid

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/admin", response_model=AdminDashboard)
async def admin_dashboard(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> AdminDashboard:
    service = DashboardService(session)
    return await service.admin()


@router.get("/employee", response_model=EmployeeDashboard)
async def employee_dashboard(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmployeeDashboard:
    repo = EmployeeRepository(session)
    emp = await repo.get_by_user_id(user.id)
    if not emp:
        raise HTTPException(status_code=404, detail="No employee profile")
    service = DashboardService(session)
    return await service.employee(emp)


@router.get("/employee/{employee_id}", response_model=EmployeeDashboard)
async def employee_dashboard_for_admin(
    employee_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> EmployeeDashboard:
    repo = EmployeeRepository(session)
    emp = await repo.get_with_user(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    service = DashboardService(session)
    return await service.employee(emp)
