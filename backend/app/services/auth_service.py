"""Authentication & registration business logic."""
from fastapi import HTTPException, status
from sqlalchemy import func as sa_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.employee import Employee, EmploymentStatus
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.auth import RegisterIn, TokenPair
from app.services.activity_service import ActivityService


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.activity = ActivityService(session)

    async def _make_tokens(self, user: User) -> TokenPair:
        access = create_access_token(
            subject=str(user.id),
            role=user.role.value,
            extra={"email": user.email},
        )
        refresh = create_refresh_token(subject=str(user.id))
        return TokenPair(access_token=access, refresh_token=refresh)

    async def register(self, data: RegisterIn) -> tuple[User, TokenPair]:
        """Open self-service registration.

        Behavior:
          * If this is the very first user in the system, they become an ADMIN
            (bootstrap). Otherwise they become an EMPLOYEE.
          * Email uniqueness is enforced.
          * An Employee profile row is always created alongside the User so the
            new account behaves identically to admin-created accounts.
        """
        # Email uniqueness
        if await self.users.get_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        # First-user-ever becomes admin; everyone else is an employee.
        existing = (
            await self.session.execute(select(sa_func.count(User.id)))
        ).scalar_one()
        role = UserRole.ADMIN if existing == 0 else UserRole.EMPLOYEE

        user = User(
            email=data.email.lower(),
            password_hash=hash_password(data.password),
            role=role,
            is_active=True,
        )
        user.employee = Employee(
            first_name=data.first_name,
            last_name=data.last_name,
            employment_status=EmploymentStatus.ACTIVE,
        )
        self.session.add(user)
        await self.session.flush()
        await self.activity.log(
            actor_id=user.id,
            action="register",
            entity_type="user",
            entity_id=str(user.id),
            metadata={"role": role.value, "bootstrap": existing == 0},
        )
        await self.session.commit()
        await self.session.refresh(user)
        return user, await self._make_tokens(user)

    async def authenticate(self, email: str, password: str) -> tuple[User, TokenPair]:
        user = await self.users.get_by_email(email)
        # Distinguish between unknown user and bad password so callers can
        # provide a clearer error message. Keep the wrong-password case as
        # 401 Unauthorized but return a clear message when the user doesn't
        # exist.
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist"
            )
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated"
            )
        await self.activity.log(
            actor_id=user.id, action="login", entity_type="user", entity_id=str(user.id)
        )
        await self.session.commit()
        return user, await self._make_tokens(user)

    async def change_password(self, user: User, current: str, new: str) -> None:
        if not verify_password(current, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
        user.password_hash = hash_password(new)
        await self.activity.log(
            actor_id=user.id,
            action="change_password",
            entity_type="user",
            entity_id=str(user.id),
        )
        await self.session.commit()
