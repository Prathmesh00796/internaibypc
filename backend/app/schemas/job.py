import uuid
from datetime import datetime

from pydantic import BaseModel


class CompanyOut(BaseModel):
    id: uuid.UUID
    name: str
    website: str | None = None
    logo_url: str | None = None

    model_config = {"from_attributes": True}


class JobOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    job_type: str
    location: str | None = None
    is_remote: bool
    stipend_min: int | None = None
    stipend_max: int | None = None
    stipend_currency: str
    skills_required: list[str] | None = None
    min_cgpa: float | None = None
    eligible_grad_years: list[int] | None = None
    freshers_only: bool
    source: str
    external_url: str
    allows_auto_submit: bool
    is_active: bool
    created_at: datetime
    company: CompanyOut | None = None

    model_config = {"from_attributes": True}


class JobWithScore(JobOut):
    match_score: float | None = None
    match_breakdown: dict | None = None


class JobSearchFilters(BaseModel):
    query: str | None = None
    work_from_home: bool | None = None
    job_type: str | None = None
    min_stipend: int | None = None
    skills: list[str] | None = None
    location: str | None = None
    graduation_year: int | None = None
    freshers_only: bool | None = None
    page: int = 1
    page_size: int = 20
