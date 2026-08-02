import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.user import User
from app.models.job import Job
from app.models.profile import Profile
from app.models.resume import Resume
from app.schemas.job import JobOut, JobWithScore
from app.api.deps import get_current_user
from app.services.matching_engine import compute_match

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobWithScore])
async def search_jobs(
    query: str | None = None,
    work_from_home: bool | None = None,
    job_type: str | None = None,
    min_stipend: int | None = None,
    location: str | None = None,
    freshers_only: bool | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Search stored jobs (populated by the scheduler / connectors) with
    filters, and attach a personalized match score for the current user.
    """
    filters = [Job.is_active == True]  # noqa: E712
    if query:
        filters.append(Job.title.ilike(f"%{query}%"))
    if work_from_home:
        filters.append(Job.is_remote == True)  # noqa: E712
    if job_type:
        filters.append(Job.job_type == job_type)
    if min_stipend is not None:
        filters.append(or_(Job.stipend_min >= min_stipend, Job.stipend_min.is_(None)))
    if location:
        filters.append(Job.location.ilike(f"%{location}%"))
    if freshers_only is not None:
        filters.append(Job.freshers_only == freshers_only)

    stmt = (
        select(Job)
        .options(selectinload(Job.company))
        .where(and_(*filters))
        .order_by(Job.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    jobs = result.scalars().all()

    # Load profile + active resume text for scoring
    profile_result = await db.execute(
        select(Profile)
        .options(selectinload(Profile.skills), selectinload(Profile.experiences))
        .where(Profile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()

    resume_text = None
    resume_skills: list[str] = []
    if profile and profile.active_resume_id:
        resume_result = await db.execute(select(Resume).where(Resume.id == profile.active_resume_id))
        resume = resume_result.scalar_one_or_none()
        if resume:
            resume_text = resume.raw_text
            if resume.parsed_data:
                resume_skills = resume.parsed_data.get("skills", [])

    output = []
    for job in jobs:
        item = JobWithScore.model_validate(job)
        if profile:
            match = compute_match(profile, resume_text, resume_skills, job)
            item.match_score = match.total_score
            item.match_breakdown = match.breakdown
        output.append(item)

    # Highest match first within the page
    output.sort(key=lambda j: j.match_score or 0, reverse=True)
    return output


@router.get("/{job_id}", response_model=JobWithScore)
async def get_job(job_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).options(selectinload(Job.company)).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile_result = await db.execute(
        select(Profile)
        .options(selectinload(Profile.skills), selectinload(Profile.experiences))
        .where(Profile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()

    item = JobWithScore.model_validate(job)
    if profile:
        resume_text, resume_skills = None, []
        if profile.active_resume_id:
            resume_result = await db.execute(select(Resume).where(Resume.id == profile.active_resume_id))
            resume = resume_result.scalar_one_or_none()
            if resume:
                resume_text = resume.raw_text
                resume_skills = (resume.parsed_data or {}).get("skills", [])
        match = compute_match(profile, resume_text, resume_skills, job)
        item.match_score = match.total_score
        item.match_breakdown = match.breakdown
    return item
