from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        stmt = (
            select(User)
            .where(User.email == email.lower(), User.is_deleted.is_(False))
            .options(selectinload(User.employee))
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_with_employee(self, user_id) -> User | None:
        stmt = select(User).where(User.id == user_id).options(selectinload(User.employee))
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
