import uuid
from datetime import datetime

from pydantic import BaseModel


class ParsedEducation(BaseModel):
    institution: str | None = None
    degree: str | None = None
    year: str | None = None
    cgpa: str | None = None


class ParsedResumeData(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = []
    projects: list[str] = []
    education: list[ParsedEducation] = []
    experience: list[str] = []
    cgpa: str | None = None
    languages: list[str] = []
    certificates: list[str] = []


class ResumeOut(BaseModel):
    id: uuid.UUID
    file_name: str
    parse_status: str
    parse_error: str | None = None
    parsed_data: dict | None = None
    is_generated: bool
    created_at: datetime

    model_config = {"from_attributes": True}
