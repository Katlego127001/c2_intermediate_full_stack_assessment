from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.activity import ActivityLog
from app.models.user import User
from app.repositories.base import BaseRepository


class ActivityRepository(BaseRepository[ActivityLog]):
    model = ActivityLog

    async def recent(self, limit: int = 10) -> list[tuple[ActivityLog, User | None]]:
        stmt = (
            select(ActivityLog)
            .options(selectinload(ActivityLog.__mapper__.relationships))
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        )
        # Join actor manually
        stmt = (
            select(ActivityLog, User)
            .join(User, User.id == ActivityLog.actor_id, isouter=True)
            .order_by(ActivityLog.created_at.desc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return [(a, u) for a, u in res.all()]

    async def latest_for_entity(self, entity_type: str, entity_id: str, action: str | None = None) -> ActivityLog | None:
        """Return the most recent activity log for a given entity (optionally filtered by action)."""
        stmt = select(ActivityLog).where(
            ActivityLog.entity_type == entity_type,
            ActivityLog.entity_id == entity_id,
        )
        if action:
            stmt = stmt.where(ActivityLog.action == action)
        stmt = stmt.order_by(ActivityLog.created_at.desc()).limit(1)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
