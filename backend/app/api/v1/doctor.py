from fastapi import APIRouter, Query

from app.api.deps import DB, Doctor
from app.schemas.session import Page, ReminderOut, SessionSummary
from app.services import session_service

router = APIRouter()


@router.get("/sessions", response_model=Page[SessionSummary])
def list_all_sessions(
    _: Doctor, db: DB, status_: str | None = Query(None, alias="status"), page: int = 1, page_size: int = 20
):
    return session_service.list_sessions(db, patient_id=None, status=status_, page=page, page_size=page_size)


@router.get("/patients/{patient_id}")
def patient_detail(patient_id: str, _: Doctor, db: DB) -> dict:
    return session_service.patient_detail(db, patient_id)


@router.get("/reminders/due", response_model=list[ReminderOut])
def due_reminders(_: Doctor, db: DB):
    from app.services import scheduler

    return scheduler.list_due(db)
