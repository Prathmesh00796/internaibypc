import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token,
)
from app.models.user import User
from app.models.profile import Profile
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, RefreshRequest, UserOut
from app.api.deps import get_current_user
from app.utils.audit import write_audit_log

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    try:
        existing = await db.execute(select(User).where(User.email == payload.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
        )
        db.add(user)
        await db.flush()

        profile = Profile(
            user_id=user.id,
            full_name=payload.full_name,
        )
        db.add(profile)

        # TEMPORARILY disable audit log
        # await write_audit_log(db, user_id=user.id, action="user.register")

        await db.commit()
        await db.refresh(user)

        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    await write_audit_log(db, user_id=user.id, action="user.login")
    await db.commit()

    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest):
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    subject = data["sub"]
    access = create_access_token(subject)
    refresh = create_refresh_token(subject)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# --- OAuth (Google/GitHub) ---
# Full OAuth code-exchange flow depends on frontend redirect wiring; this
# endpoint shape is provided as the integration point. Given a verified
# provider token from the frontend's OAuth redirect, we find-or-create
# the user and issue our own JWTs (never store the provider's password).
@router.post("/oauth/{provider}", response_model=TokenResponse)
async def oauth_login(provider: str, id_token: str, db: AsyncSession = Depends(get_db)):
    if provider not in ("google", "github"):
        raise HTTPException(status_code=400, detail="Unsupported provider")
    raise HTTPException(
        status_code=501,
        detail=(
            f"OAuth token verification for '{provider}' is not configured. "
            "Set GOOGLE_CLIENT_ID/GITHUB_CLIENT_ID and implement token verification "
            "in app/services/oauth_service.py."
        ),
    )
