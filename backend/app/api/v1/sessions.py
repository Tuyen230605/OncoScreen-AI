"""Sessions (patient) + review (doctor). Router mỏng — logic ở services/session_service & hitl_service."""

from fastapi import APIRouter, Query, status

from app.api.deps import DB, CurrentUser, Doctor, Patient
from app.schemas.session import AnswersIn, Page, ReviewIn, SessionOut, SessionSummary
from app.services import hitl_service, session_service

router = APIRouter()


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(user: Patient, db: DB):
    return await session_service.create_session(db, user)


@router.get("", response_model=Page[SessionSummary])
def list_my_sessions(
    user: Patient, db: DB, status_: str | None = Query(None, alias="status"), page: int = 1, page_size: int = 20
):
    return session_service.list_sessions(db, patient_id=user.id, status=status_, page=page, page_size=page_size)


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: str, user: CurrentUser, db: DB):
    return session_service.get_session_for(db, session_id, user)


@router.post("/{session_id}/answers", response_model=SessionOut)
async def submit_answers(session_id: str, body: AnswersIn, user: Patient, db: DB):
    return await session_service.submit_answers(db, session_id, user, body.answers)


@router.post("/{session_id}/review", response_model=SessionOut)
def review(session_id: str, body: ReviewIn, doctor: Doctor, db: DB):
    return hitl_service.review(db, session_id, doctor, body)
