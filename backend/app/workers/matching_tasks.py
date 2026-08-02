"""
After a scheduled search saves new Job rows, this task scores them
against every active user's profile and creates Application rows
(status=MATCHED) for high-scoring matches, then queues a notification.
"""
from datetime import datetime, timedelta, timezone

from celery import shared_task
from sqlalchemy import select, and_

from app.core.database import get_sync_db
from app.core.logging_config import logger
from app.models.user import User
from app.models.profile import Profile
from app.models.resume import Resume
from app.models.job import Job
from app.models.application import Application, ApplicationStatus
from app.services.matching_engine import compute_match

MATCH_NOTIFY_THRESHOLD = 70.0  # only notify users about strong matches


@shared_task(name="app.workers.matching_tasks.match_new_jobs_for_all_users")
def match_new_jobs_for_all_users():
    db = next(get_sync_db())
    try:
        # Only consider jobs created in the last day to avoid rescoring the whole table
        cutoff = datetime.now(timezone.utc) - timedelta(days=1)
        recent_jobs = db.execute(select(Job).where(Job.created_at >= cutoff, Job.is_active == True)).scalars().all()  # noqa: E712
        if not recent_jobs:
            return {"matched_users": 0}

        users = db.execute(select(User).where(User.is_active == True)).scalars().all()  # noqa: E712

        notify_count = 0
        for user in users:
            profile = db.execute(select(Profile).where(Profile.user_id == user.id)).scalar_one_or_none()
            if not profile:
                continue

            resume_text, resume_skills = None, []
            if profile.active_resume_id:
                resume = db.execute(select(Resume).where(Resume.id == profile.active_resume_id)).scalar_one_or_none()
                if resume:
                    resume_text = resume.raw_text
                    resume_skills = (resume.parsed_data or {}).get("skills", [])

            for job in recent_jobs:
                # Skip if an application record already exists for this user+job
                existing = db.execute(
                    select(Application).where(and_(Application.user_id == user.id, Application.job_id == job.id))
                ).scalar_one_or_none()
                if existing:
                    continue

                match = compute_match(profile, resume_text, resume_skills, job)

                application = Application(
                    user_id=user.id,
                    job_id=job.id,
                    status=ApplicationStatus.MATCHED,
                    match_score=match.total_score,
                    match_breakdown=match.breakdown,
                )
                db.add(application)

                if match.total_score >= MATCH_NOTIFY_THRESHOLD:
                    from app.workers.notification_tasks import notify_new_job_match
                    notify_new_job_match.delay(str(user.id), str(job.id), match.total_score)
                    notify_count += 1

            db.commit()

        logger.info(f"Matching complete: {len(recent_jobs)} jobs scored against {len(users)} users, {notify_count} notifications queued")
        return {"jobs_scored": len(recent_jobs), "users": len(users), "notifications_queued": notify_count}
    finally:
        db.close()
