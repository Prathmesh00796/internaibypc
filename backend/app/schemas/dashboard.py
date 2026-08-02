from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_jobs_found: int
    applications_prepared: int
    applications_submitted: int
    pending_review: int
    response_rate: float  # % of submitted apps that got any response (interview/offer/rejection)
    interviews: int
    rejections: int
    offers: int


class TimeSeriesPoint(BaseModel):
    period: str  # e.g. "2026-07-01" or "2026-W30" or "2026-07"
    applications: int
    interviews: int
    offers: int
    rejections: int


class AnalyticsOverview(BaseModel):
    daily: list[TimeSeriesPoint]
    weekly: list[TimeSeriesPoint]
    monthly: list[TimeSeriesPoint]
    top_companies: list[dict]
    top_skills: list[dict]
    response_rate: float
    interview_rate: float
    offer_rate: float
