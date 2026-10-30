from fastapi import APIRouter, HTTPException, status

from app.api.deps import DB, Patient
from app.models import PatientProfile
from app.schemas.patient import PatientProfileIn, PatientProfileOut
from app.schemas.record import PatientRecordOut
from app.services import record_service

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
    profile.lifestyle = body.lifestyle.model_dump(exclude_none=True)
    db.add(profile)
    record_service.add_event(db, user.id, "profile.updated", "Bệnh nhân cập nhật hồ sơ sức khoẻ.", actor_id=user.id)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me/record", response_model=PatientRecordOut)
def my_record(user: Patient, db: DB):
    return record_service.record_out(db, user, user)
