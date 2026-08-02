import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import encrypt_field, decrypt_field
from app.models.user import User
from app.models.profile import Profile, Skill, Project, Experience
from app.schemas.profile import (
    ProfileOut, ProfileUpdate, SkillIn, SkillOut, ProjectIn, ProjectOut,
    ExperienceIn, ExperienceOut,
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])


async def _get_profile_or_404(db: AsyncSession, user_id: uuid.UUID) -> Profile:
    result = await db.execute(
        select(Profile)
        .options(selectinload(Profile.skills), selectinload(Profile.projects), selectinload(Profile.experiences))
        .where(Profile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


def _to_profile_out(profile: Profile) -> ProfileOut:
    data = ProfileOut.model_validate(profile)
    data.phone = decrypt_field(profile.phone_encrypted) if profile.phone_encrypted else None
    return data


@router.get("", response_model=ProfileOut)
async def get_profile(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profile = await _get_profile_or_404(db, current_user.id)
    return _to_profile_out(profile)


@router.put("", response_model=ProfileOut)
async def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile_or_404(db, current_user.id)

    update_data = payload.model_dump(exclude_unset=True)
    if "phone" in update_data:
        phone = update_data.pop("phone")
        profile.phone_encrypted = encrypt_field(phone) if phone else None

    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile, attribute_names=["skills", "projects", "experiences"])
    return _to_profile_out(profile)


# --- Skills ---
@router.post("/skills", response_model=SkillOut, status_code=201)
async def add_skill(payload: SkillIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profile = await _get_profile_or_404(db, current_user.id)
    skill = Skill(profile_id=profile.id, name=payload.name, proficiency=payload.proficiency, source="manual")
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    return skill


@router.delete("/skills/{skill_id}", status_code=204)
async def delete_skill(skill_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profile = await _get_profile_or_404(db, current_user.id)
    result = await db.execute(select(Skill).where(Skill.id == skill_id, Skill.profile_id == profile.id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    await db.delete(skill)
    await db.commit()


# --- Projects ---
@router.post("/projects", response_model=ProjectOut, status_code=201)
async def add_project(payload: ProjectIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profile = await _get_profile_or_404(db, current_user.id)
    project = Project(profile_id=profile.id, **payload.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(project_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profile = await _get_profile_or_404(db, current_user.id)
    result = await db.execute(select(Project).where(Project.id == project_id, Project.profile_id == profile.id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()


# --- Experience ---
@router.post("/experience", response_model=ExperienceOut, status_code=201)
async def add_experience(payload: ExperienceIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profile = await _get_profile_or_404(db, current_user.id)
    experience = Experience(profile_id=profile.id, **payload.model_dump())
    db.add(experience)
    await db.commit()
    await db.refresh(experience)
    return experience


@router.delete("/experience/{experience_id}", status_code=204)
async def delete_experience(experience_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profile = await _get_profile_or_404(db, current_user.id)
    result = await db.execute(
        select(Experience).where(Experience.id == experience_id, Experience.profile_id == profile.id)
    )
    experience = result.scalar_one_or_none()
    if not experience:
        raise HTTPException(status_code=404, detail="Experience not found")
    await db.delete(experience)
    await db.commit()
