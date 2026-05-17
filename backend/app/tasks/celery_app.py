"""Celery app factory & background task definitions."""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "jobtracker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.celery_app"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
)


@celery_app.task(name="tasks.send_overdue_reminders")
def send_overdue_reminders() -> dict:
    """Stub: in real life, query overdue jobs & send email/push."""
    # Kept side-effect-free here to avoid coupling worker to DB session lifecycle.
    return {"status": "ok", "sent": 0}


@celery_app.task(name="tasks.audit_cleanup")
def audit_cleanup(days: int = 90) -> dict:
    """Stub: purge old activity logs."""
    return {"status": "ok", "days": days}


celery_app.conf.beat_schedule = {
    "overdue-reminders-hourly": {
        "task": "tasks.send_overdue_reminders",
        "schedule": crontab(minute=0),
    },
    "audit-cleanup-daily": {
        "task": "tasks.audit_cleanup",
        "schedule": crontab(minute=0, hour=3),
        "args": (90,),
    },
}
