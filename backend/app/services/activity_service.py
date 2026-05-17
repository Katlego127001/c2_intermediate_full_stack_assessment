"""Audit/activity logging — write-side."""
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import ActivityLog


class ActivityService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(
        self,
        *,
        actor_id=None,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ActivityLog:
        entry = ActivityLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            metadata_=metadata,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry
