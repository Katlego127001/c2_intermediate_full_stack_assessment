"""WebSocket endpoint — real-time notifications."""
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import decode_token
from app.models.user import UserRole
from app.repositories.user import UserRepository
from app.websockets.manager import ws_manager

router = APIRouter(tags=["websockets"])


async def _resolve_user(token: str):
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
    except JWTError:
        return None
    async with AsyncSessionLocal() as session:  # type: AsyncSession
        users = UserRepository(session)
        return await users.get_with_employee(user_id)


@router.websocket("/ws/notifications")
async def notifications(ws: WebSocket, token: str = Query(...)):
    user = await _resolve_user(token)
    if not user or not user.is_active:
        await ws.close(code=4401)
        return

    employee_id = user.employee.id if user.employee else None

    if user.role == UserRole.ADMIN:
        await ws_manager.connect_admin(ws)
    elif employee_id:
        await ws_manager.connect_employee(employee_id, ws)
    else:
        await ws.close(code=4403)
        return

    try:
        while True:
            # Listen for client pings to keep connection alive
            await ws.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(ws, employee_id=employee_id)
