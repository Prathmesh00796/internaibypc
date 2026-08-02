"""
Celery application + periodic task schedule.

Three daily search windows (morning/afternoon/night) as specced, plus
supporting maintenance tasks. Run with:
  celery -A app.workers.celery_app worker --loglevel=info
  celery -A app.workers.celery_app beat --loglevel=info
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "internai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.search_tasks",
        "app.workers.resume_tasks",
        "app.workers.notification_tasks",
        "app.workers.matching_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60 * 30,  # hard kill after 30 min
    task_soft_time_limit=60 * 25,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=60,  # 1 min backoff between retries
)

celery_app.conf.beat_schedule = {
    "search-morning": {
        "task": "app.workers.search_tasks.run_scheduled_search",
        "schedule": crontab(hour=7, minute=0),
        "args": ("morning",),
    },
    "search-afternoon": {
        "task": "app.workers.search_tasks.run_scheduled_search",
        "schedule": crontab(hour=13, minute=0),
        "args": ("afternoon",),
    },
    "search-night": {
        "task": "app.workers.search_tasks.run_scheduled_search",
        "schedule": crontab(hour=20, minute=0),
        "args": ("night",),
    },
    "daily-report": {
        "task": "app.workers.notification_tasks.send_daily_reports",
        "schedule": crontab(hour=21, minute=0),
    },
}
