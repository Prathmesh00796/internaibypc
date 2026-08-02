from fastapi import APIRouter

from app.api.routes import auth, profile, resumes, jobs, applications, dashboard, notifications, admin

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(profile.router)
api_router.include_router(resumes.router)
api_router.include_router(jobs.router)
api_router.include_router(applications.router)
api_router.include_router(dashboard.router)
api_router.include_router(notifications.router)
api_router.include_router(admin.router)
