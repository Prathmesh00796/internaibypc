"""
Resume parsing background task. Kicked off immediately after upload so
the HTTP request returns fast; profile auto-fill happens once parsing
completes.
"""
import uuid

from celery import shared_task
from sqlalchemy import select

from app.core.database import get_sync_db
from app.core.logging_config import logger
from app.models.resume import Resume, ResumeParseStatus
from app.models.profile import Profile, Skill
from app.services.resume_parser import parse_resume
from app.services.storage_service import get_storage_backend


@shared_task(bind=True, max_retries=3, name="app.workers.resume_tasks.parse_resume_task")
def parse_resume_task(self, resume_id: str):
    db = next(get_sync_db())
    try:
        resume = db.execute(select(Resume).where(Resume.id == uuid.UUID(resume_id))).scalar_one_or_none()
        if not resume:
            logger.warning(f"Resume {resume_id} not found for parsing")
            return

        resume.parse_status = ResumeParseStatus.PROCESSING
        db.commit()

        storage = get_storage_backend()
        local_path = storage.get_local_path(resume.storage_path)

        parsed = parse_resume(local_path)

        resume.parsed_data = parsed.to_dict()
        resume.raw_text = parsed.raw_text
        resume.parse_status = ResumeParseStatus.COMPLETED
        db.commit()

        _autofill_profile_from_resume(db, resume)

    except Exception as exc:
        logger.exception(f"Resume parsing failed for {resume_id}: {exc}")
        db.rollback()
        resume = db.execute(select(Resume).where(Resume.id == uuid.UUID(resume_id))).scalar_one_or_none()
        if resume:
            resume.parse_status = ResumeParseStatus.FAILED
            resume.parse_error = str(exc)
            db.commit()
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()


def _autofill_profile_from_resume(db, resume: Resume) -> None:
    """
    Populate empty profile fields from parsed resume data. We only fill
    fields the user hasn't already set, and we always add parsed skills
    as new Skill rows tagged source='resume_parsed' rather than
    overwriting manually-entered skills.
    """
    profile = db.execute(select(Profile).where(Profile.user_id == resume.user_id)).scalar_one_or_none()
    if not profile or not resume.parsed_data:
        return

    data = resume.parsed_data

    if not profile.full_name and data.get("name"):
        profile.full_name = data["name"]

    if data.get("cgpa") and profile.cgpa is None:
        try:
            profile.cgpa = float(str(data["cgpa"]).split("/")[0])
        except (ValueError, IndexError):
            pass

    existing_skill_names = {s.name.lower() for s in profile.skills}
    for skill_name in data.get("skills", []):
        if skill_name.lower() not in existing_skill_names:
            db.add(Skill(profile_id=profile.id, name=skill_name, source="resume_parsed"))
            existing_skill_names.add(skill_name.lower())

    extra = profile.extra_data or {}
    extra["languages"] = data.get("languages", [])
    extra["certificates"] = data.get("certificates", [])
    extra["parsed_education"] = data.get("education", [])
    extra["parsed_experience"] = data.get("experience", [])
    extra["parsed_projects"] = data.get("projects", [])
    profile.extra_data = extra

    if profile.active_resume_id is None:
        profile.active_resume_id = resume.id

    db.commit()
