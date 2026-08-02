import enum
import uuid

from sqlalchemy import String, Float, ForeignKey, Text, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class ApplicationStatus(str, enum.Enum):
    MATCHED = "matched"                # found + scored, not yet actioned
    QUEUED_FOR_REVIEW = "queued_for_review"   # prepared, waiting on user confirmation
    SAVED = "saved"                     # user saved for later
    SKIPPED = "skipped"                 # user dismissed
    READY_TO_SUBMIT = "ready_to_submit"  # autofilled, awaiting final user click
    SUBMITTED = "submitted"             # successfully applied (auto or user-confirmed)
    FAILED = "failed"                   # submission attempt failed
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Application(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "applications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.MATCHED, nullable=False, index=True
    )

    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-100
    match_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # per-factor scores

    cover_letter_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    autofill_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # prepared form data

    submitted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    requires_manual_submission: Mapped[bool] = mapped_column(default=True)
    submission_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="applications")
    job: Mapped["Job"] = relationship("Job", back_populates="applications")
    history: Mapped[list["ApplicationStatusHistory"]] = relationship(
        "ApplicationStatusHistory", back_populates="application", cascade="all, delete-orphan"
    )


class ApplicationStatusHistory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Audit trail of every status transition for an application."""
    __tablename__ = "application_status_history"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    application: Mapped["Application"] = relationship("Application", back_populates="history")
