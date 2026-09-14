from fastapi import APIRouter, HTTPException, status

from app.api.deps import DB, Patient
from app.models import PatientProfile
from app.schemas.patient import PatientProfileIn, PatientProfileOut

router = APIRouter()


@router.get("/me/profile", response_model=PatientProfileOut)
def get_profile(user: Patient, db: DB):
    profile = db.get(PatientProfile, user.id)
    if not profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Chưa có hồ sơ")
    return profile


@router.put("/me/profile", response_model=PatientProfileOut)
def upsert_profile(body: PatientProfileIn, user: Patient, db: DB):
    profile = db.get(PatientProfile, user.id) or PatientProfile(user_id=user.id)
    profile.age = body.age
    profile.gender = body.gender.value
    profile.genetics_history = body.genetics_history
    profile.lifestyle = body.lifestyle
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
