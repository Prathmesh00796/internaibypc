"""
Aggregation queries backing the dashboard and analytics endpoints.
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.job import Job, Company


async def get_dashboard_stats(db: AsyncSession, user_id: uuid.UUID) -> dict:
    base = select(Application).where(Application.user_id == user_id)

    total_jobs_found_result = await db.execute(
        select(func.count(Application.id)).where(Application.user_id == user_id)
    )
    total_jobs_found = total_jobs_found_result.scalar() or 0

    async def count_status(*statuses: ApplicationStatus) -> int:
        result = await db.execute(
            select(func.count(Application.id)).where(
                and_(Application.user_id == user_id, Application.status.in_(statuses))
            )
        )
        return result.scalar() or 0

    applications_prepared = await count_status(
        ApplicationStatus.QUEUED_FOR_REVIEW, ApplicationStatus.READY_TO_SUBMIT,
        ApplicationStatus.SUBMITTED, ApplicationStatus.INTERVIEW,
        ApplicationStatus.OFFER, ApplicationStatus.REJECTED,
    )
    applications_submitted = await count_status(
        ApplicationStatus.SUBMITTED, ApplicationStatus.INTERVIEW,
        ApplicationStatus.OFFER, ApplicationStatus.REJECTED,
    )
    pending_review = await count_status(ApplicationStatus.QUEUED_FOR_REVIEW, ApplicationStatus.READY_TO_SUBMIT)
    interviews = await count_status(ApplicationStatus.INTERVIEW)
    rejections = await count_status(ApplicationStatus.REJECTED)
    offers = await count_status(ApplicationStatus.OFFER)

    responded = interviews + rejections + offers
    response_rate = round(100 * responded / applications_submitted, 1) if applications_submitted else 0.0

    return {
        "total_jobs_found": total_jobs_found,
        "applications_prepared": applications_prepared,
        "applications_submitted": applications_submitted,
        "pending_review": pending_review,
        "response_rate": response_rate,
        "interviews": interviews,
        "rejections": rejections,
        "offers": offers,
    }


async def _time_series(db: AsyncSession, user_id: uuid.UUID, days_back: int, date_trunc: str) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days_back)
    period_expr = func.date_trunc(date_trunc, Application.created_at)

    result = await db.execute(
        select(
            period_expr.label("period"),
            func.count(Application.id).label("applications"),
            func.count(Application.id).filter(Application.status == ApplicationStatus.INTERVIEW).label("interviews"),
            func.count(Application.id).filter(Application.status == ApplicationStatus.OFFER).label("offers"),
            func.count(Application.id).filter(Application.status == ApplicationStatus.REJECTED).label("rejections"),
        )
        .where(and_(Application.user_id == user_id, Application.created_at >= since))
        .group_by(period_expr)
        .order_by(period_expr)
    )
    rows = result.all()
    return [
        {
            "period": row.period.strftime("%Y-%m-%d") if date_trunc == "day" else row.period.strftime("%Y-%m-%d"),
            "applications": row.applications,
            "interviews": row.interviews,
            "offers": row.offers,
            "rejections": row.rejections,
        }
        for row in rows
    ]


async def get_analytics_overview(db: AsyncSession, user_id: uuid.UUID) -> dict:
    daily = await _time_series(db, user_id, days_back=30, date_trunc="day")
    weekly = await _time_series(db, user_id, days_back=180, date_trunc="week")
    monthly = await _time_series(db, user_id, days_back=730, date_trunc="month")

    top_companies_result = await db.execute(
        select(Company.name, func.count(Application.id).label("count"))
        .join(Job, Job.company_id == Company.id)
        .join(Application, Application.job_id == Job.id)
        .where(Application.user_id == user_id)
        .group_by(Company.name)
        .order_by(func.count(Application.id).desc())
        .limit(5)
    )
    top_companies = [{"name": r.name, "count": r.count} for r in top_companies_result.all()]

    top_skills_result = await db.execute(
        select(func.unnest(Job.skills_required).label("skill"), func.count().label("count"))
        .join(Application, Application.job_id == Job.id)
        .where(Application.user_id == user_id)
        .group_by("skill")
        .order_by(func.count().desc())
        .limit(10)
    )
    top_skills = [{"name": r.skill, "count": r.count} for r in top_skills_result.all() if r.skill]

    stats = await get_dashboard_stats(db, user_id)
    submitted = stats["applications_submitted"] or 1
    interview_rate = round(100 * stats["interviews"] / submitted, 1)
    offer_rate = round(100 * stats["offers"] / submitted, 1)

    return {
        "daily": daily,
        "weekly": weekly,
        "monthly": monthly,
        "top_companies": top_companies,
        "top_skills": top_skills,
        "response_rate": stats["response_rate"],
        "interview_rate": interview_rate,
        "offer_rate": offer_rate,
    }
