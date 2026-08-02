import enum

from sqlalchemy import String, Integer, Enum, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class SchedulerRunStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class SchedulerRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Log of each scheduled search run (morning/afternoon/night) for observability."""
    __tablename__ = "scheduler_runs"

    run_type: Mapped[str] = mapped_column(String(50), nullable=False)  # morning | afternoon | night | manual
    status: Mapped[SchedulerRunStatus] = mapped_column(Enum(SchedulerRunStatus), default=SchedulerRunStatus.RUNNING)

    jobs_found: Mapped[int] = mapped_column(Integer, default=0)
    jobs_new: Mapped[int] = mapped_column(Integer, default=0)
    jobs_duplicate: Mapped[int] = mapped_column(Integer, default=0)
    users_notified: Mapped[int] = mapped_column(Integer, default=0)

    started_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    error_log: Mapped[str | None] = mapped_column(Text, nullable=True)
