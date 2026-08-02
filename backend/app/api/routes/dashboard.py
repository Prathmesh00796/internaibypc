from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardStats, AnalyticsOverview
from app.api.deps import get_current_user
from app.services.analytics_service import get_dashboard_stats, get_analytics_overview

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def dashboard_stats(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stats = await get_dashboard_stats(db, current_user.id)
    return stats


@router.get("/analytics", response_model=AnalyticsOverview)
async def dashboard_analytics(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    data = await get_analytics_overview(db, current_user.id)
    return data
