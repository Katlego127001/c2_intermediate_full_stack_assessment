"""Auth endpoints — register, login, logout, change password, me."""
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordIn,
    CurrentUser,
    LoginIn,
    RegisterIn,
    TokenPair,
)
from app.schemas.common import Message
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterIn, session: AsyncSession = Depends(get_db)) -> TokenPair:
    """Open self-service registration.

    * First-ever user becomes an admin (bootstrap).
    * All subsequent registrations default to the `employee` role.
      Admins may later elevate a user's role via the employees endpoints.
    """
    service = AuthService(session)
    _, tokens = await service.register(payload)
    return tokens


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginIn, session: AsyncSession = Depends(get_db)) -> TokenPair:
    service = AuthService(session)
    _, tokens = await service.authenticate(payload.email, payload.password)
    return tokens


@router.post("/login/oauth", response_model=TokenPair, include_in_schema=False)
async def login_oauth_form(
    form: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_db)
) -> TokenPair:
    """OAuth2 form-encoded login — used by Swagger 'Authorize' button."""
    service = AuthService(session)
    _, tokens = await service.authenticate(form.username, form.password)
    return tokens


@router.post("/logout", response_model=Message)
async def logout(_: User = Depends(get_current_user)) -> Message:
    """Stateless JWT — frontend simply discards tokens. Endpoint exists for audit/UX."""
    return Message(message="Logged out")


@router.post("/change-password", response_model=Message)
async def change_password(
    payload: ChangePasswordIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Message:
    service = AuthService(session)
    await service.change_password(user, payload.current_password, payload.new_password)
    return Message(message="Password updated")


@router.get("/me", response_model=CurrentUser)
async def me(user: User = Depends(get_current_user)) -> CurrentUser:
    emp = user.employee
    return CurrentUser(
        id=str(user.id),
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        employee_id=str(emp.id) if emp else None,
        full_name=(f"{emp.first_name} {emp.last_name}" if emp else None),
    )
