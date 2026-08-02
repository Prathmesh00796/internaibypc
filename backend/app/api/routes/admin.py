import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.job import Job, Company
from app.models.application import Application, ApplicationStatus
from app.models.audit_log import AuditLog
from app.models.scheduler_run import SchedulerRun
from app.api.deps import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users")
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return result.scalars().all()


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(user_id: uuid.UUID, _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await db.commit()
    return {"ok": True}


@router.patch("/users/{user_id}/reactivate")
async def reactivate_user(user_id: uuid.UUID, _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    await db.commit()
    return {"ok": True}


@router.get("/jobs")
async def list_jobs_admin(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Job).order_by(Job.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return result.scalars().all()


@router.patch("/jobs/{job_id}/deactivate")
async def deactivate_job(job_id: uuid.UUID, _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.is_active = False
    await db.commit()
    return {"ok": True}


@router.get("/companies")
async def list_companies(_: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).order_by(Company.name))
    return result.scalars().all()


@router.get("/scheduler-runs")
async def list_scheduler_runs(
    limit: int = Query(default=20, ge=1, le=100),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SchedulerRun).order_by(SchedulerRun.created_at.desc()).limit(limit))
    return result.scalars().all()


@router.get("/audit-logs")
async def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit))
    return result.scalars().all()


@router.get("/stats")
async def platform_stats(_: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    total_jobs = (await db.execute(select(func.count(Job.id)))).scalar()
    total_applications = (await db.execute(select(func.count(Application.id)))).scalar()
    total_submitted = (
        await db.execute(
            select(func.count(Application.id)).where(
                Application.status.in_([ApplicationStatus.SUBMITTED, ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER])
            )
        )
    ).scalar()

    return {
        "total_users": total_users,
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "total_submitted": total_submitted,
    }
