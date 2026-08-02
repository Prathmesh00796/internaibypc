"""
Application lifecycle service.

Central place enforcing the platform's compliance rule: automated
submission is only ever attempted when
  (a) the job's source connector declares supports_auto_submit=True, AND
  (b) job.allows_auto_submit is True (set per-listing from the source), AND
  (c) the user has explicitly confirmed THIS application via the
      review-queue confirm endpoint.
Every other case prepares the application (autofill payload + cover
letter) and stops at ApplicationStatus.READY_TO_SUBMIT, requiring the
user to click "Submit" themselves (possibly on the external site).
"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import logger
from app.models.application import Application, ApplicationStatus, ApplicationStatusHistory
from app.models.job import Job
from app.models.profile import Profile
from app.services.cover_letter_generator import generate_cover_letter


def build_autofill_payload(profile: Profile, job: Job) -> dict:
    """
    Construct the data a browser extension / user would use to fill an
    external application form. We never submit this automatically unless
    explicitly permitted (see module docstring).
    """
    return {
        "full_name": profile.full_name,
        "email": profile.user.email if profile.user else None,
        "location": profile.location,
        "college": profile.college,
        "degree": profile.degree,
        "graduation_year": profile.graduation_year,
        "cgpa": profile.cgpa,
        "linkedin_url": profile.linkedin_url,
        "github_url": profile.github_url,
        "portfolio_url": profile.portfolio_url,
        "skills": [s.name for s in profile.skills],
        "resume_id": str(profile.active_resume_id) if profile.active_resume_id else None,
    }


async def prepare_application(
    db: AsyncSession, application: Application, profile: Profile, job: Job
) -> Application:
    """Fill in cover letter + autofill payload; move to review/ready state."""
    application.cover_letter_text = generate_cover_letter(profile, job)
    application.autofill_payload = build_autofill_payload(profile, job)

    can_auto_submit = job.allows_auto_submit  # gated further at confirm time
    application.requires_manual_submission = not can_auto_submit

    old_status = application.status
    application.status = (
        ApplicationStatus.READY_TO_SUBMIT if can_auto_submit else ApplicationStatus.QUEUED_FOR_REVIEW
    )

    db.add(ApplicationStatusHistory(
        application_id=application.id, from_status=old_status.value,
        to_status=application.status.value, note="Application prepared (autofill + cover letter generated)",
    ))
    await db.flush()
    return application


async def confirm_and_submit(db: AsyncSession, application: Application, user_confirmed: bool) -> Application:
    """
    Final step before an application counts as SUBMITTED. Even for
    auto-submit-eligible jobs, we require `user_confirmed=True` from an
    explicit user action — no application is ever sent silently.
    """
    if not user_confirmed:
        logger.info(f"Application {application.id} submission not confirmed by user; leaving as-is")
        return application

    old_status = application.status
    application.status = ApplicationStatus.SUBMITTED
    application.submitted_at = datetime.now(timezone.utc)

    db.add(ApplicationStatusHistory(
        application_id=application.id, from_status=old_status.value,
        to_status=application.status.value, note="User confirmed submission",
    ))
    await db.flush()
    return application
