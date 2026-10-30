"""Khám với Clinical Copilot + HITL: bác sĩ xem brief, hỏi Copilot, sửa/duyệt kế hoạch rồi kết thúc khám (S4)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from time import monotonic

from ai_core.api import CANCER_LABEL_VI
from ai_core.guardrails.disclaimer import COPILOT_DISCLAIMER_VI, DISCLAIMER_VI
from ai_core.guardrails.safety import GuardrailViolation, validate_plan
from ai_core.schemas import ClinicalBrief, QuestionAnswer, ScreeningPlan
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Appointment, AuditLog, Encounter, Reminder, User
from app.schemas.appointment import ReminderOut
from app.schemas.auth import UserOut
from app.schemas.encounter import CopilotAskIn, EncounterOut, FinalizeEncounterIn
from app.services import agent_service, record_service, scheduler
from app.services.appointment_service import services_by_code


def to_out(db: Session, e: Encounter, viewer: User) -> EncounterOut:
    """★ Quy tắc lộ dữ liệu: bệnh nhân KHÔNG thấy brief/draft/clinical_notes; kết quả chỉ hiện khi finalized."""
    is_doctor = viewer.role == "doctor"
    finalized = e.status == "finalized"
    patient = db.get(User, e.patient_id)
    doctor = db.get(User, e.doctor_id) if e.doctor_id else None
    reminders = db.scalars(select(Reminder).where(Reminder.encounter_id == e.id).order_by(Reminder.due_date)).all()
    return EncounterOut(
        id=e.id,
        appointment_id=e.appointment_id,
        patient_id=e.patient_id,
        patient_name=patient.full_name if patient else "?",
        doctor=UserOut.model_validate(doctor) if doctor else None,
        status=e.status,
        brief=e.brief if is_doctor else None,
        draft_plan=e.draft_plan if is_doctor else None,
        final_plan=e.final_plan if (is_doctor or finalized) else None,
        clinical_notes=e.clinical_notes if is_doctor else None,
        conclusion=e.conclusion if (is_doctor or finalized) else None,
        finalized_at=e.finalized_at,
        created_at=e.created_at,
        reminders=[ReminderOut.model_validate(r) for r in reminders] if (is_doctor or finalized) else [],
        disclaimer=COPILOT_DISCLAIMER_VI if is_doctor else DISCLAIMER_VI,
    )


def _get_or_404(db: Session, encounter_id: str) -> Encounter:
    e = db.get(Encounter, encounter_id)
    if not e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy lần khám")
    return e


def _require_owner(e: Encounter, doctor: User) -> None:
    """HITL: chỉ bác sĩ đã bắt đầu lần khám (đã đọc brief) mới được sinh lại brief hay kết thúc khám."""
    if e.doctor_id != doctor.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ bác sĩ phụ trách lần khám này mới được thực hiện")


async def _generate_brief(db: Session, e: Encounter, a: Appointment) -> None:
    patient = db.get(User, e.patient_id)
    reason = a.reason or services_by_code().get(a.service_code, {}).get("name")
    record = record_service.build_ai_record(db, patient, reason)
    started = monotonic()
    brief: ClinicalBrief = await agent_service.build_brief(record)
    agent_service.record_run(
        db,
        "copilot",
        trace_id=brief.trace_id,
        events=brief.trace_events,
        started=started,
        patient_id=e.patient_id,
        encounter_id=e.id,
        red_flag=bool(brief.red_flags),
    )
    e.brief = brief.model_dump(mode="json")
    e.draft_plan = brief.draft_plan.model_dump(mode="json") if brief.draft_plan else None
    e.trace_id = brief.trace_id


async def start(db: Session, doctor: User, appointment_id: str) -> EncounterOut:
    a = db.get(Appointment, appointment_id)
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy lịch hẹn")
    existing = db.scalar(select(Encounter).where(Encounter.appointment_id == a.id))
    if existing:
        return to_out(db, existing, doctor)
    if a.status not in ("requested", "confirmed"):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Lịch hẹn đang ở trạng thái {a.status}")
    if a.status == "requested":
        a.status, a.scheduled_date = "confirmed", a.scheduled_date or date.today()
    a.doctor_id = doctor.id
    e = Encounter(appointment_id=a.id, patient_id=a.patient_id, doctor_id=doctor.id, status="in_progress")
    db.add(e)
    db.flush()
    service = services_by_code().get(a.service_code, {}).get("name", a.service_code)
    record_service.add_event(
        db,
        a.patient_id,
        "encounter.started",
        f"Bắt đầu khám: {service} ({doctor.full_name}).",
        ref_type="encounter",
        ref_id=e.id,
        actor_id=doctor.id,
    )
    await _generate_brief(db, e, a)
    db.add(AuditLog(actor_id=doctor.id, action="encounter.start", entity="encounter", entity_id=e.id))
    db.commit()
    db.refresh(e)
    return to_out(db, e, doctor)


def get_for(db: Session, encounter_id: str, viewer: User) -> EncounterOut:
    e = _get_or_404(db, encounter_id)
    if viewer.role == "patient" and e.patient_id != viewer.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy lần khám")
    return to_out(db, e, viewer)


async def regenerate_brief(db: Session, doctor: User, encounter_id: str) -> EncounterOut:
    e = _get_or_404(db, encounter_id)
    _require_owner(e, doctor)
    if e.status == "finalized":
        raise HTTPException(status.HTTP_409_CONFLICT, "Lần khám đã kết thúc")
    await _generate_brief(db, e, db.get(Appointment, e.appointment_id))
    db.commit()
    db.refresh(e)
    return to_out(db, e, doctor)


async def ask_copilot(db: Session, doctor: User, encounter_id: str, body: CopilotAskIn) -> QuestionAnswer:
    e = _get_or_404(db, encounter_id)
    a = db.get(Appointment, e.appointment_id)
    record = record_service.build_ai_record(db, db.get(User, e.patient_id), a.reason if a else None)
    started = monotonic()
    answer = await agent_service.ask_copilot(body.question, record, body.history)
    agent_service.record_run(
        db,
        "copilot_qa",
        trace_id=answer.trace_id,
        events=answer.trace_events,
        started=started,
        patient_id=e.patient_id,
        encounter_id=e.id,
        insufficient_evidence=answer.insufficient_evidence,
    )
    db.commit()
    return answer


def finalize(db: Session, doctor: User, encounter_id: str, body: FinalizeEncounterIn) -> EncounterOut:
    e = _get_or_404(db, encounter_id)
    _require_owner(e, doctor)
    if e.status == "finalized":
        raise HTTPException(status.HTTP_409_CONFLICT, "Lần khám đã kết thúc")
    a = db.get(Appointment, e.appointment_id)
    if a is None or a.status != "confirmed":
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Lịch hẹn đang ở trạng thái {a.status if a else 'không tồn tại'}"
        )
    explicit_no_plan = "final_plan" in body.model_fields_set and body.final_plan is None
    if body.final_plan is not None:
        final = body.final_plan
    elif explicit_no_plan or not body.use_draft:
        final = None
    else:
        final = ScreeningPlan.model_validate(e.draft_plan) if e.draft_plan else None
    if final is not None:
        try:
            validate_plan(final)  # bác sĩ sửa vẫn phải qua guardrail (nguồn, ngôn ngữ)
        except GuardrailViolation as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Kế hoạch vi phạm guardrail: {exc}") from exc
    final_json = final.model_dump(mode="json") if final else None
    if final_json != e.draft_plan:  # R5: mọi khác biệt so với bản nháp (kể cả bỏ bản nháp) đều được kiểm toán
        db.add(
            AuditLog(
                actor_id=doctor.id,
                action="plan.edit",
                entity="encounter",
                entity_id=e.id,
                before=e.draft_plan,
                after=final_json,
            )
        )
    e.final_plan = final_json
    e.conclusion = body.conclusion
    e.clinical_notes = body.clinical_notes
    e.status = "finalized"
    e.finalized_at = datetime.now(UTC)
    reminders = scheduler.create_reminders_for_plan(db, e, final) if final else []
    a.status = "completed"
    cancer_types = sorted({item.cancer_type.value for item in final.items}) if final else []
    plan_text = (
        "Kế hoạch theo dõi: " + "; ".join(f"{CANCER_LABEL_VI[i.cancer_type]} — {i.method}" for i in final.items) + "."
        if final
        else "Không lập kế hoạch tầm soát định kỳ."
    )
    record_service.add_event(
        db,
        e.patient_id,
        "encounter.finalized",
        f"Kết luận của bác sĩ: {body.conclusion[:300]} {plan_text}",
        data={"cancer_types": cancer_types, "reminders": len(reminders)},
        ref_type="encounter",
        ref_id=e.id,
        actor_id=doctor.id,
    )
    db.add(AuditLog(actor_id=doctor.id, action="encounter.finalize", entity="encounter", entity_id=e.id))
    db.commit()
    db.refresh(e)
    return to_out(db, e, doctor)


async def ask_patient_question(db: Session, patient: User, encounter_id: str, question: str) -> QuestionAnswer:
    e = _get_or_404(db, encounter_id)
    if e.patient_id != patient.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy lần khám")
    if e.status != "finalized":
        raise HTTPException(status.HTTP_409_CONFLICT, "Chỉ có thể hỏi về kế hoạch đã được bác sĩ duyệt")
    plan = ScreeningPlan.model_validate(e.final_plan) if e.final_plan else None
    started = monotonic()
    answer = await agent_service.answer_question(question, plan)
    agent_service.record_run(
        db,
        "patient_qa",
        trace_id=answer.trace_id,
        events=answer.trace_events,
        started=started,
        patient_id=patient.id,
        encounter_id=e.id,
        insufficient_evidence=answer.insufficient_evidence,
    )
    db.commit()
    return answer.model_copy(update={"trace_events": []})  # R4: trace chỉ lưu ở agent_runs, không lộ cho bệnh nhân
