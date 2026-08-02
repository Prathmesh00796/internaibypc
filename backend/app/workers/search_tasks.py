"""
Scheduled search tasks. Runs three times daily (morning/afternoon/night)
per the spec: fetches listings from all active job source connectors,
deduplicates against existing Job rows (by source + external_id), saves
new listings, then triggers per-user matching + notification.
"""
import asyncio
from datetime import datetime, timezone

from celery import shared_task
from sqlalchemy import select

from app.core.database import get_sync_db
from app.core.logging_config import logger
from app.models.job import Job, Company, JobSource
from app.models.scheduler_run import SchedulerRun, SchedulerRunStatus
from app.services.job_sources.registry import get_active_connectors


def _run_async(coro):
    """Helper to run the async connector fetch methods from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(bind=True, max_retries=2, name="app.workers.search_tasks.run_scheduled_search")
def run_scheduled_search(self, run_type: str = "manual"):
    db = next(get_sync_db())
    run = SchedulerRun(run_type=run_type, status=SchedulerRunStatus.RUNNING, started_at=datetime.now(timezone.utc))
    db.add(run)
    db.commit()
    db.refresh(run)

    jobs_found = 0
    jobs_new = 0
    jobs_duplicate = 0
    errors = []

    try:
        connectors = get_active_connectors()
        for connector in connectors:
            try:
                listings = _run_async(connector.fetch_listings())
            except Exception as exc:
                logger.error(f"Connector {connector.source} failed: {exc}")
                errors.append(f"{connector.source}: {exc}")
                continue

            jobs_found += len(listings)

            for listing in listings:
                existing = db.execute(
                    select(Job).where(Job.source == connector.source, Job.external_id == listing.external_id)
                ).scalar_one_or_none()

                if existing:
                    jobs_duplicate += 1
                    continue

                company = db.execute(select(Company).where(Company.name == listing.company_name)).scalar_one_or_none()
                if not company:
                    company = Company(name=listing.company_name)
                    db.add(company)
                    db.flush()

                job = Job(
                    company_id=company.id,
                    title=listing.title,
                    description=listing.description,
                    job_type=listing.job_type,
                    location=listing.location,
                    is_remote=listing.is_remote,
                    stipend_min=listing.stipend_min,
                    stipend_max=listing.stipend_max,
                    skills_required=listing.skills_required,
                    min_cgpa=listing.min_cgpa,
                    eligible_grad_years=listing.eligible_grad_years,
                    freshers_only=listing.freshers_only,
                    source=connector.source,
                    external_id=listing.external_id,
                    external_url=listing.external_url,
                    allows_auto_submit=connector.supports_auto_submit,
                    raw_source_data=listing.raw,
                )
                db.add(job)
                jobs_new += 1

            db.commit()

        run.status = SchedulerRunStatus.SUCCESS if not errors else SchedulerRunStatus.PARTIAL
        run.jobs_found = jobs_found
        run.jobs_new = jobs_new
        run.jobs_duplicate = jobs_duplicate
        run.finished_at = datetime.now(timezone.utc)
        if errors:
            run.error_log = "\n".join(errors)
        db.commit()

        logger.info(f"Scheduled search [{run_type}] complete: {jobs_new} new, {jobs_duplicate} duplicate, {len(errors)} errors")

        # Chain into matching + notification for users, only if we found something new
        if jobs_new > 0:
            from app.workers.matching_tasks import match_new_jobs_for_all_users
            match_new_jobs_for_all_users.delay()

        return {"jobs_found": jobs_found, "jobs_new": jobs_new, "jobs_duplicate": jobs_duplicate}

    except Exception as exc:
        logger.exception(f"Scheduled search [{run_type}] failed: {exc}")
        run.status = SchedulerRunStatus.FAILED
        run.error_log = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        raise self.retry(exc=exc, countdown=120)
    finally:
        db.close()
