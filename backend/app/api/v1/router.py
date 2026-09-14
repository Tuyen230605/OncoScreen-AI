from fastapi import APIRouter

from app.api.v1 import auth, doctor, education, health, patients, reminders, sessions

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(patients.router, prefix="/patients", tags=["patients"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(doctor.router, prefix="/doctor", tags=["doctor"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["reminders"])
api_router.include_router(education.router, prefix="/education", tags=["education"])
