import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.user import User
from app.models.job import Job
from app.models.profile import Profile
from app.models.application import Application, ApplicationStatus, ApplicationStatusHistory
from app.schemas.application import ApplicationOut, ApplicationAction, ApplicationConfirmSubmit
from app.api.deps import get_current_user
from app.services.application_service import prepare_application, confirm_and_submit
from app.services.cover_letter_generator import generate_cover_letter
from app.utils.audit import write_audit_log

router = APIRouter(prefix="/applications", tags=["applications"])


async def _get_profile(db: AsyncSession, user_id: uuid.UUID) -> Profile:
    result = await db.execute(
        select(Profile)
        .options(selectinload(Profile.skills), selectinload(Profile.projects), selectinload(Profile.experiences))
        .where(Profile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found — complete your profile first")
    return profile


@router.get("", response_model=list[ApplicationOut])
async def list_applications(
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [Application.user_id == current_user.id]
    if status_filter:
        filters.append(Application.status == status_filter)

    result = await db.execute(
        select(Application)
        .options(selectinload(Application.job).selectinload(Job.company))
        .where(and_(*filters))
        .order_by(Application.created_at.desc())
    )
    return result.scalars().all()


@router.get("/queue", response_model=list[ApplicationOut])
async def get_review_queue(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Applications awaiting user review/confirmation before submission."""
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.job).selectinload(Job.company))
        .where(
            and_(
                Application.user_id == current_user.id,
                Application.status.in_([ApplicationStatus.QUEUED_FOR_REVIEW, ApplicationStatus.READY_TO_SUBMIT]),
            )
        )
        .order_by(Application.match_score.desc())
    )
    return result.scalars().all()


@router.post("/{job_id}/action", response_model=ApplicationOut)
async def act_on_job(
    job_id: uuid.UUID,
    payload: ApplicationAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Apply / Skip / Save from the job list. "Apply" prepares the
    application (autofill + cover letter) and places it in the review
    queue (or ready-to-submit if the source explicitly permits auto-submit) —
    it does NOT submit anything on its own.
    """
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing_result = await db.execute(
        select(Application).where(Application.user_id == current_user.id, Application.job_id == job_id)
    )
    application = existing_result.scalar_one_or_none()
    if not application:
        application = Application(user_id=current_user.id, job_id=job_id, status=ApplicationStatus.MATCHED)
        db.add(application)
        await db.flush()

    if payload.action == "skip":
        old_status = application.status
        application.status = ApplicationStatus.SKIPPED
        db.add(ApplicationStatusHistory(application_id=application.id, from_status=old_status.value, to_status="skipped"))
    elif payload.action == "save":
        old_status = application.status
        application.status = ApplicationStatus.SAVED
        db.add(ApplicationStatusHistory(application_id=application.id, from_status=old_status.value, to_status="saved"))
    elif payload.action == "apply":
        profile = await _get_profile(db, current_user.id)
        if profile.active_resume_id is None:
            raise HTTPException(status_code=400, detail="Set an active resume before applying")
        application.resume_id = profile.active_resume_id
        application = await prepare_application(db, application, profile, job)
    else:
        raise HTTPException(status_code=400, detail="action must be one of: apply, skip, save")

    await db.commit()
    await db.refresh(application, attribute_names=["job"])
    return application


@router.post("/{application_id}/confirm-submit", response_model=ApplicationOut)
async def confirm_submit(
    application_id: uuid.UUID,
    payload: ApplicationConfirmSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Final human-in-the-loop confirmation. This is the ONLY endpoint that
    can move an application to SUBMITTED — required even for sources
    that support automated submission, per platform ToS compliance.
    """
    result = await db.execute(
        select(Application).where(Application.id == application_id, Application.user_id == current_user.id)
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.status not in (ApplicationStatus.QUEUED_FOR_REVIEW, ApplicationStatus.READY_TO_SUBMIT):
        raise HTTPException(status_code=400, detail=f"Application is not ready to submit (status={application.status.value})")

    if payload.submission_notes:
        application.submission_notes = payload.submission_notes

    application = await confirm_and_submit(db, application, user_confirmed=payload.confirmed)
    await write_audit_log(
        db, user_id=current_user.id, action="application.submit",
        resource_type="application", resource_id=str(application.id),
    )
    await db.commit()
    await db.refresh(application, attribute_names=["job"])
    return application


@router.post("/{application_id}/regenerate-cover-letter", response_model=ApplicationOut)
async def regenerate_cover_letter(
    application_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.job).selectinload(Job.company))
        .where(Application.id == application_id, Application.user_id == current_user.id)
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    profile = await _get_profile(db, current_user.id)
    application.cover_letter_text = generate_cover_letter(profile, application.job)
    await db.commit()
    await db.refresh(application, attribute_names=["job"])
    return application


@router.patch("/{application_id}/status", response_model=ApplicationOut)
async def update_status(
    application_id: uuid.UUID,
    new_status: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Manually update status (e.g. mark interview/offer/rejected) —
    used when the user hears back outside the platform's own tracking.
    """
    valid_statuses = {s.value for s in ApplicationStatus}
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

    result = await db.execute(
        select(Application).where(Application.id == application_id, Application.user_id == current_user.id)
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    old_status = application.status
    application.status = ApplicationStatus(new_status)
    db.add(ApplicationStatusHistory(application_id=application.id, from_status=old_status.value, to_status=new_status))

    await db.commit()
    await db.refresh(application, attribute_names=["job"])
    return application
