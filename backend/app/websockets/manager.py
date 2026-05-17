"""In-memory WebSocket connection manager (single-process).

For multi-replica production, swap with a Redis pub/sub fanout. The public
interface (`connect/disconnect/notify_employee/broadcast_admins`) is stable
so the swap is opaque to callers.
"""
import asyncio
import uuid
from typing import Any

from fastapi import WebSocket

from app.core.logging import get_logger

log = get_logger("ws")


class ConnectionManager:
    def __init__(self) -> None:
        self._employee_conns: dict[uuid.UUID, set[WebSocket]] = {}
        self._admin_conns: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect_employee(self, employee_id: uuid.UUID, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._employee_conns.setdefault(employee_id, set()).add(ws)
        log.info("ws.connect.employee", employee_id=str(employee_id))

    async def connect_admin(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._admin_conns.add(ws)
        log.info("ws.connect.admin")

    async def disconnect(self, ws: WebSocket, *, employee_id: uuid.UUID | None = None) -> None:
        async with self._lock:
            if employee_id and employee_id in self._employee_conns:
                self._employee_conns[employee_id].discard(ws)
                if not self._employee_conns[employee_id]:
                    self._employee_conns.pop(employee_id, None)
            self._admin_conns.discard(ws)
        log.info("ws.disconnect")

    async def notify_employee(self, employee_id: uuid.UUID, payload: dict[str, Any]) -> None:
        conns = list(self._employee_conns.get(employee_id, set()))
        for ws in conns:
            try:
                await ws.send_json(payload)
            except Exception:  # noqa: BLE001
                pass
        # Admins also receive a copy (for ops awareness)
        await self.broadcast_admins({"scope": "employee", "employee_id": str(employee_id), **payload})

    async def broadcast_admins(self, payload: dict[str, Any]) -> None:
        for ws in list(self._admin_conns):
            try:
                await ws.send_json(payload)
            except Exception:  # noqa: BLE001
                pass


ws_manager = ConnectionManager()
