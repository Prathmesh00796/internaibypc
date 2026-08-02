"""
Notification dispatch tasks: new job matches, status changes, and the
daily summary report.
"""
import uuid
from datetime import datetime, timedelta, timezone

from celery import shared_task
from sqlalchemy import select, and_

from app.core.database import get_sync_db
from app.core.logging_config import logger
from app.models.user import User
from app.models.job import Job
from app.models.application import Application, ApplicationStatus
from app.models.notification import Notification, NotificationType, NotificationChannel
from app.services.notification_service import send_email, NOTIFICATION_TEMPLATES


@shared_task(name="app.workers.notification_tasks.notify_new_job_match")
def notify_new_job_match(user_id: str, job_id: str, match_score: float):
    db = next(get_sync_db())
    try:
        user = db.execute(select(User).where(User.id == uuid.UUID(user_id))).scalar_one_or_none()
        job = db.execute(select(Job).where(Job.id == uuid.UUID(job_id))).scalar_one_or_none()
        if not user or not job:
            return

        ctx = {
            "job_title": job.title,
            "company": job.company.name if job.company else "a company",
            "match_score": match_score,
            "url": job.external_url,
        }
        subject, body_html = NOTIFICATION_TEMPLATES["new_job"](ctx)

        notification = Notification(
            user_id=user.id, type=NotificationType.NEW_JOB, channel=NotificationChannel.EMAIL,
            title=subject, body=body_html,
        )
        db.add(notification)
        db.commit()

        try:
            send_email(user.email, subject, body_html)
            notification.is_sent = True
        except Exception as exc:
            logger.error(f"Failed to send new-job email to {user.email}: {exc}")
            notification.send_error = str(exc)
        db.commit()
    finally:
        db.close()


@shared_task(name="app.workers.notification_tasks.notify_status_change")
def notify_status_change(user_id: str, job_id: str, notification_type: str):
    """notification_type in {'interview', 'offer', 'rejection'}"""
    db = next(get_sync_db())
    try:
        user = db.execute(select(User).where(User.id == uuid.UUID(user_id))).scalar_one_or_none()
        job = db.execute(select(Job).where(Job.id == uuid.UUID(job_id))).scalar_one_or_none()
        if not user or not job or notification_type not in NOTIFICATION_TEMPLATES:
            return

        ctx = {"job_title": job.title, "company": job.company.name if job.company else "a company"}
        subject, body_html = NOTIFICATION_TEMPLATES[notification_type](ctx)

        notification = Notification(
            user_id=user.id, type=NotificationType(notification_type), channel=NotificationChannel.EMAIL,
            title=subject, body=body_html,
        )
        db.add(notification)
        db.commit()

        try:
            send_email(user.email, subject, body_html)
            notification.is_sent = True
        except Exception as exc:
            notification.send_error = str(exc)
        db.commit()
    finally:
        db.close()


@shared_task(name="app.workers.notification_tasks.send_daily_reports")
def send_daily_reports():
    db = next(get_sync_db())
    try:
        since = datetime.now(timezone.utc) - timedelta(days=1)
        users = db.execute(select(User).where(User.is_active == True)).scalars().all()  # noqa: E712

        sent = 0
        for user in users:
            new_jobs = db.execute(
                select(Application).where(and_(Application.user_id == user.id, Application.created_at >= since))
            ).scalars().all()
            pending = db.execute(
                select(Application).where(
                    and_(
                        Application.user_id == user.id,
                        Application.status.in_([ApplicationStatus.QUEUED_FOR_REVIEW, ApplicationStatus.READY_TO_SUBMIT]),
                    )
                )
            ).scalars().all()

            if not new_jobs and not pending:
                continue  # don't spam users with an empty report

            ctx = {"new_jobs": len(new_jobs), "pending_review": len(pending)}
            subject, body_html = NOTIFICATION_TEMPLATES["daily_report"](ctx)

            notification = Notification(
                user_id=user.id, type=NotificationType.DAILY_REPORT, channel=NotificationChannel.EMAIL,
                title=subject, body=body_html,
            )
            db.add(notification)
            db.commit()

            try:
                send_email(user.email, subject, body_html)
                notification.is_sent = True
                sent += 1
            except Exception as exc:
                notification.send_error = str(exc)
            db.commit()

        logger.info(f"Daily reports sent to {sent} users")
        return {"sent": sent}
    finally:
        db.close()
