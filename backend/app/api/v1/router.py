"""v1 API aggregator."""
from fastapi import APIRouter

from app.api.v1.routes import auth, dashboard, employees, jobs, ws

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(employees.router)
api_router.include_router(jobs.router)
api_router.include_router(dashboard.router)
api_router.include_router(ws.router)
