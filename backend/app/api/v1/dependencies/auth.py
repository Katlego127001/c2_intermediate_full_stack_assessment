"""Auth-related FastAPI dependencies (current user, role guards)."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db)
) -> User:
    creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise creds_exc
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise creds_exc
    except JWTError as exc:
        raise creds_exc from exc

    users = UserRepository(session)
    user = await users.get_with_employee(user_id)
    if not user or user.is_deleted:
        raise creds_exc
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive")
    return user


def require_role(*roles: UserRole):
    """Dependency factory that enforces RBAC."""

    async def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges"
            )
        return user

    return _checker


require_admin = require_role(UserRole.ADMIN)
require_employee = require_role(UserRole.EMPLOYEE)
require_any = require_role(UserRole.ADMIN, UserRole.EMPLOYEE)
