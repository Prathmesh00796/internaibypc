import uuid
from datetime import date

from pydantic import BaseModel, Field


class SkillOut(BaseModel):
    id: uuid.UUID
    name: str
    proficiency: str | None = None
    source: str

    model_config = {"from_attributes": True}


class SkillIn(BaseModel):
    name: str
    proficiency: str | None = None


class ProjectIn(BaseModel):
    title: str
    description: str | None = None
    tech_stack: list[str] | None = None
    url: str | None = None


class ProjectOut(ProjectIn):
    id: uuid.UUID
    model_config = {"from_attributes": True}


class ExperienceIn(BaseModel):
    company_name: str
    role: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False


class ExperienceOut(ExperienceIn):
    id: uuid.UUID
    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    location: str | None = None
    college: str | None = None
    degree: str | None = None
    graduation_year: int | None = None
    cgpa: float | None = Field(default=None, ge=0, le=10)
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    cover_letter_default: str | None = None
    preferred_roles: list[str] | None = None
    preferred_locations: list[str] | None = None
    preferred_job_type: str | None = None
    preferred_stipend_min: int | None = None
    work_from_home_only: bool | None = None
    fresher_only: bool | None = None


class ProfileOut(BaseModel):
    id: uuid.UUID
    full_name: str | None = None
    phone: str | None = None  # decrypted on the way out
    location: str | None = None
    college: str | None = None
    degree: str | None = None
    graduation_year: int | None = None
    cgpa: float | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    cover_letter_default: str | None = None
    preferred_roles: list[str] | None = None
    preferred_locations: list[str] | None = None
    preferred_job_type: str | None = None
    preferred_stipend_min: int | None = None
    work_from_home_only: bool
    fresher_only: bool
    active_resume_id: uuid.UUID | None = None
    skills: list[SkillOut] = []
    projects: list[ProjectOut] = []
    experiences: list[ExperienceOut] = []

    model_config = {"from_attributes": True}
