"""Generic async repository base class."""
from typing import Generic, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: Type[ModelT]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id_):
        return await self.session.get(self.model, id_)

    async def list(self, *, limit: int = 50, offset: int = 0):
        stmt = select(self.model).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def count(self, *where) -> int:
        stmt = select(func.count()).select_from(self.model)
        for clause in where:
            stmt = stmt.where(clause)
        res = await self.session.execute(stmt)
        return int(res.scalar_one())

    async def add(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def delete(self, obj: ModelT) -> None:
        await self.session.delete(obj)
        await self.session.flush()
