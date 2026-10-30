"""Bác sĩ: hàng chờ lịch hẹn, hồ sơ xuyên suốt, Clinical Copilot, kết thúc khám (HITL), quan sát AI."""

from ai_core.schemas import QuestionAnswer
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.api.deps import DB, Doctor
from app.models import Appointment, PatientProfile, RecordEvent, User
from app.schemas.appointment import AppointmentOut, ConfirmAppointmentIn, ReminderOut
from app.schemas.auth import UserOut
from app.schemas.common import Page
from app.schemas.encounter import CopilotAskIn, EncounterOut, FinalizeEncounterIn
from app.schemas.metrics import AgentRunOut, MetricsOut
from app.schemas.patient import PatientProfileOut
from app.schemas.record import PatientListItem, PatientRecordOut
from app.services import appointment_service, encounter_service, metrics_service, record_service, scheduler

router = APIRouter()
MAX_PAGE_SIZE = 100


@router.get("/appointments", response_model=Page[AppointmentOut])
def appointments(
    _: Doctor,
    db: DB,
    status_: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
):
    return appointment_service.list_for_doctor(db, status_, page, page_size)


@router.post("/appointments/{appointment_id}/confirm", response_model=AppointmentOut)
def confirm(appointment_id: str, body: ConfirmAppointmentIn, doctor: Doctor, db: DB):
    return appointment_service.confirm(db, doctor, appointment_id, body.scheduled_date)


@router.post("/appointments/{appointment_id}/start", response_model=EncounterOut)
async def start(appointment_id: str, doctor: Doctor, db: DB):
    return await encounter_service.start(db, doctor, appointment_id)


@router.get("/patients", response_model=list[PatientListItem])
def patients(_: Doctor, db: DB, q: str | None = None):
    query = select(User).where(User.role == "patient")
    if q:
        like = f"%{q.lower()}%"
        query = query.where(or_(func.lower(User.full_name).like(like), func.lower(User.email).like(like)))
    out = []
    for user in db.scalars(query.order_by(User.created_at.desc()).limit(100)).all():
        profile = db.get(PatientProfile, user.id)
        open_count = db.scalar(
            select(func.count())
            .select_from(Appointment)
            .where(Appointment.patient_id == user.id, Appointment.status.in_(["requested", "confirmed"]))
        )
        last = db.scalar(select(func.max(RecordEvent.occurred_at)).where(RecordEvent.patient_id == user.id))
        out.append(
            PatientListItem(
                user=UserOut.model_validate(user),
                profile=PatientProfileOut.model_validate(profile) if profile else None,
                open_appointments=open_count or 0,
                last_activity=last,
            )
        )
    return out


@router.get("/patients/{patient_id}/record", response_model=PatientRecordOut)
def patient_record(patient_id: str, doctor: Doctor, db: DB):
    patient = db.get(User, patient_id)
    if not patient or patient.role != "patient":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy bệnh nhân")
    return record_service.record_out(db, patient, doctor)


@router.get("/encounters/{encounter_id}", response_model=EncounterOut)
def encounter(encounter_id: str, doctor: Doctor, db: DB):
    return encounter_service.get_for(db, encounter_id, doctor)


@router.post("/encounters/{encounter_id}/brief", response_model=EncounterOut)
async def regenerate_brief(encounter_id: str, doctor: Doctor, db: DB):
    return await encounter_service.regenerate_brief(db, doctor, encounter_id)


@router.post("/encounters/{encounter_id}/copilot", response_model=QuestionAnswer)
async def copilot(encounter_id: str, body: CopilotAskIn, doctor: Doctor, db: DB):
    return await encounter_service.ask_copilot(db, doctor, encounter_id, body)


@router.post("/encounters/{encounter_id}/finalize", response_model=EncounterOut)
def finalize(encounter_id: str, body: FinalizeEncounterIn, doctor: Doctor, db: DB):
    return encounter_service.finalize(db, doctor, encounter_id, body)


@router.get("/metrics", response_model=MetricsOut)
def metrics(_: Doctor, db: DB):
    return metrics_service.metrics(db)


@router.get("/agent-runs", response_model=Page[AgentRunOut])
def agent_runs(
    _: Doctor,
    db: DB,
    agent: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
):
    return metrics_service.agent_runs(db, agent, page, page_size)


@router.get("/reminders/due", response_model=list[ReminderOut])
def due_reminders(_: Doctor, db: DB):
    return scheduler.list_due(db)
