import uuid
from datetime import date

from sqlalchemy import String, Integer, Float, ForeignKey, Text, ARRAY, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin, TimestampMixin


class Profile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Core profile info. Sensitive fields (phone) are stored encrypted
    at the application layer (see app.core.security.encrypt_field).
    """
    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_encrypted: Mapped[str | None] = mapped_column(String(512), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    college: Mapped[str | None] = mapped_column(String(255), nullable=True)
    degree: Mapped[str | None] = mapped_column(String(255), nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)

    linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    cover_letter_default: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Preferences ---
    preferred_roles: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    preferred_locations: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    preferred_job_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # internship/full-time
    preferred_stipend_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    work_from_home_only: Mapped[bool] = mapped_column(default=False)
    fresher_only: Mapped[bool] = mapped_column(default=True)

    # Free-form structured extras extracted from resume parsing (languages, certs, etc.)
    extra_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    active_resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")
    skills: Mapped[list["Skill"]] = relationship(
        "Skill", back_populates="profile", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="profile", cascade="all, delete-orphan"
    )
    experiences: Mapped[list["Experience"]] = relationship(
        "Experience", back_populates="profile", cascade="all, delete-orphan"
    )


class Skill(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "skills"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    proficiency: Mapped[str | None] = mapped_column(String(50), nullable=True)  # beginner/intermediate/advanced
    source: Mapped[str] = mapped_column(String(20), default="manual")  # manual | resume_parsed

    profile: Mapped["Profile"] = relationship("Profile", back_populates="skills")


class Project(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "projects"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tech_stack: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    profile: Mapped["Profile"] = relationship("Profile", back_populates="projects")


class Experience(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "experiences"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(default=False)

    profile: Mapped["Profile"] = relationship("Profile", back_populates="experiences")
