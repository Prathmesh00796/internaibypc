import enum
import uuid

from sqlalchemy import String, Integer, Text, ForeignKey, Boolean, Enum, ARRAY, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class JobType(str, enum.Enum):
    INTERNSHIP = "internship"
    FULL_TIME = "full_time"
    PART_TIME = "part_time"


class JobSource(str, enum.Enum):
    """
    Where a job listing came from. Each source has a corresponding
    connector in app.services.job_sources implementing a shared interface.
    Automated *submission* is only enabled for sources whose ToS/API
    explicitly permit it (see PlatformConnection.supports_auto_submit).
    """
    INTERNSHALA = "internshala"
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    NAUKRI = "naukri"
    COMPANY_CAREERS_PAGE = "company_careers_page"
    GREENHOUSE_API = "greenhouse_api"
    LEVER_API = "lever_api"
    MANUAL = "manual"


class Company(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)

    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="company")


class Job(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_job_source_external_id"),
    )

    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_type: Mapped[JobType] = mapped_column(Enum(JobType), default=JobType.INTERNSHIP)

    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)

    stipend_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stipend_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stipend_currency: Mapped[str] = mapped_column(String(10), default="INR")

    skills_required: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    min_cgpa: Mapped[float | None] = mapped_column(nullable=True)
    eligible_grad_years: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), nullable=True)
    freshers_only: Mapped[bool] = mapped_column(Boolean, default=False)

    source: Mapped[JobSource] = mapped_column(Enum(JobSource), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    external_url: Mapped[str] = mapped_column(String(1024), nullable=False)

    # Whether this source permits automated application submission
    # per its API terms / ToS. Default false = manual review required.
    allows_auto_submit: Mapped[bool] = mapped_column(Boolean, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # still open / not expired
    raw_source_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="jobs")
    applications: Mapped[list["Application"]] = relationship("Application", back_populates="job")
