"""
Import all models here so Alembic's autogenerate can discover them
via Base.metadata, and so other modules can do `from app.models import X`.
"""
from app.models.user import User
from app.models.profile import Profile, Skill, Project, Experience
from app.models.resume import Resume
from app.models.job import Job, Company
from app.models.application import Application, ApplicationStatusHistory
from app.models.platform_connection import PlatformConnection
from app.models.notification import Notification
from app.models.audit_log import AuditLog
from app.models.scheduler_run import SchedulerRun

__all__ = [
    "User",
    "Profile",
    "Skill",
    "Project",
    "Experience",
    "Resume",
    "Job",
    "Company",
    "Application",
    "ApplicationStatusHistory",
    "PlatformConnection",
    "Notification",
    "AuditLog",
    "SchedulerRun",
]
