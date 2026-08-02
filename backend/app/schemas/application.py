import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.job import JobOut


class ApplicationAction(BaseModel):
    action: str  # "apply" | "skip" | "save"


class ApplicationConfirmSubmit(BaseModel):
    confirmed: bool
    submission_notes: str | None = None


class ApplicationOut(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    status: str
    match_score: float | None = None
    match_breakdown: dict | None = None
    cover_letter_text: str | None = None
    autofill_payload: dict | None = None
    requires_manual_submission: bool
    submitted_at: datetime | None = None
    created_at: datetime
    job: JobOut | None = None

    model_config = {"from_attributes": True}


class ApplicationStatusUpdate(BaseModel):
    status: str
    note: str | None = None
