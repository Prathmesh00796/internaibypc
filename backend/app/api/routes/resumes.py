import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import io

from app.core.database import get_db
from app.core.logging_config import logger
from app.models.user import User
from app.models.profile import Profile
from app.models.resume import Resume, ResumeParseStatus
from app.schemas.resume import ResumeOut
from app.api.deps import get_current_user
from app.services.storage_service import get_storage_backend
from app.services.resume_generator import generate_resume_pdf
from app.workers.resume_tasks import parse_resume_task

router = APIRouter(prefix="/resumes", tags=["resumes"])

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
ALLOWED_CONTENT_TYPES = {"application/pdf"}


@router.post("/upload", response_model=ResumeOut, status_code=201)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File exceeds 5MB limit")

    storage = get_storage_backend()
    storage_path = storage.save(contents, file.filename, subdir="resumes")

    resume = Resume(
        user_id=current_user.id,
        file_name=file.filename,
        storage_path=storage_path,
        file_size_bytes=len(contents),
        parse_status=ResumeParseStatus.PENDING,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)

    # Kick off async parsing so the upload response returns immediately.
    parse_resume_task.delay(str(resume.id))

    return resume


@router.get("", response_model=list[ResumeOut])
async def list_resumes(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Resume).where(Resume.user_id == current_user.id).order_by(Resume.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{resume_id}", response_model=ResumeOut)
async def get_resume(resume_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume


@router.post("/{resume_id}/set-active", response_model=ResumeOut)
async def set_active_resume(
    resume_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    profile_result = await db.execute(select(Profile).where(Profile.user_id == current_user.id))
    profile = profile_result.scalar_one_or_none()
    if profile:
        profile.active_resume_id = resume.id

    await db.commit()
    await db.refresh(resume)
    return resume


@router.delete("/{resume_id}", status_code=204)
async def delete_resume(resume_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == current_user.id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")

    storage = get_storage_backend()
    try:
        storage.delete(resume.storage_path)
    except Exception as exc:
        logger.warning(f"Failed to delete stored file for resume {resume_id}: {exc}")

    await db.delete(resume)
    await db.commit()


@router.post("/generate", status_code=201)
async def generate_ats_resume(
    template: str = Query(default="classic", pattern="^(classic|modern)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an ATS-friendly PDF resume from the user's saved profile and stream it back."""
    result = await db.execute(
        select(Profile)
        .options(selectinload(Profile.skills), selectinload(Profile.projects), selectinload(Profile.experiences))
        .where(Profile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    pdf_bytes = generate_resume_pdf(profile, template=template)

    filename = f"{(profile.full_name or 'resume').replace(' ', '_')}_resume.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
