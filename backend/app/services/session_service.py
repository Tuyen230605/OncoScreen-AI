"""Luồng session: tạo → trả lời → red-flag / screening. Serializer áp dụng quy tắc lộ dữ liệu theo role (R1)."""

from __future__ import annotations

from ai_core.guardrails.disclaimer import DISCLAIMER_VI
from ai_core.schemas import Answer, PatientContext
from ai_core.schemas import PatientProfile as AIProfile
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AuditLog, PatientProfile, Reminder, ScreeningSession, User
from app.schemas.auth import UserOut
from app.schemas.patient import PatientProfileOut
from app.schemas.session import Page, ReminderOut, SessionOut, SessionSummary
from app.services import agent_service

# ------------------------------------------------------------------ helpers


def _ai_profile(profile: PatientProfile) -> AIProfile:
    return AIProfile(
        age=profile.age,
        gender=profile.gender,
        genetics_history=profile.genetics_history or [],
        lifestyle=profile.lifestyle or {},
        lifestyle_score=profile.lifestyle_score,
    )


def _require_profile(db: Session, user: User) -> PatientProfile:
    profile = db.get(PatientProfile, user.id)
    if not profile:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Vui lòng điền hồ sơ trước khi bắt đầu đánh giá")
    return profile


def _get_or_404(db: Session, session_id: str) -> ScreeningSession:
    s = db.get(ScreeningSession, session_id)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiên")
    return s


def _log(db: Session, session: ScreeningSession, actor: User, action: str, before=None, after=None) -> None:
    db.add(AuditLog(session_id=session.id, actor_id=actor.id, action=action, before=before, after=after))


# ------------------------------------------------------------------ serializers


def to_summary(db: Session, s: ScreeningSession) -> SessionSummary:
    patient = db.get(User, s.patient_id)
    return SessionSummary(
        id=s.id,
        patient_id=s.patient_id,
        patient_name=patient.full_name if patient else "?",
        status=s.status,
        created_at=s.created_at,
        updated_at=s.updated_at,
        has_red_flag=bool(s.red_flags and s.red_flags.get("detected")),
    )


def to_session_out(db: Session, s: ScreeningSession, viewer: User) -> SessionOut:
    """★ Quy tắc lộ dữ liệu (API_CONTRACT §3): patient KHÔNG BAO GIỜ thấy draft_plan;
    final_plan / risk_assessment chỉ khi approved. Doctor thấy tất cả."""
    is_doctor = viewer.role == "doctor"
    approved = s.status == "approved"
    reviewer = db.get(User, s.doctor_id) if s.doctor_id else None
    reminders = db.scalars(select(Reminder).where(Reminder.session_id == s.id).order_by(Reminder.due_date)).all()
    base = to_summary(db, s)
    return SessionOut(
        **base.model_dump(),
        questionnaire=s.questionnaire if s.status == "collecting" else None,
        answers=[Answer.model_validate(a) for a in (s.answers or [])],
        red_flag=s.red_flags,
        risk_assessment=s.risk_assessment if (is_doctor or approved) else None,
        draft_plan=s.draft_plan if is_doctor else None,
        final_plan=s.final_plan if (is_doctor or approved) else None,
        doctor_note=s.doctor_note,
        reviewed_by=UserOut.model_validate(reviewer) if reviewer else None,
        reviewed_at=s.reviewed_at,
        disclaimer=DISCLAIMER_VI,
        reminders=[ReminderOut.model_validate(r) for r in reminders] if approved else [],
    )


# ------------------------------------------------------------------ use cases


async def create_session(db: Session, user: User) -> SessionOut:
    profile = _require_profile(db, user)
    questionnaire = await agent_service.get_questionnaire(_ai_profile(profile))
    s = ScreeningSession(patient_id=user.id, status="collecting", questionnaire=questionnaire.model_dump(mode="json"))
    db.add(s)
    _log(db, s, user, "session.create")
    db.commit()
    db.refresh(s)
    return to_session_out(db, s, user)


async def submit_answers(db: Session, session_id: str, user: User, new_answers: list[Answer]) -> SessionOut:
    s = _get_or_404(db, session_id)
    if s.patient_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiên")
    if s.status != "collecting":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Phiên đang ở trạng thái {s.status}")

    # merge answers (câu mới ghi đè câu cũ cùng id)
    merged = {a["question_id"]: a for a in (s.answers or [])}
    for a in new_answers:
        merged[a.question_id] = a.model_dump(mode="json")
    s.answers = list(merged.values())
    answers = [Answer.model_validate(a) for a in s.answers]
    _log(db, s, user, "session.answer", after={"count": len(answers)})

    # 1) red-flag — luôn chạy trước (S3)
    rf = await agent_service.check_red_flags(answers)
    if rf.detected:
        s.status = "red_flag"
        s.red_flags = rf.model_dump(mode="json")
        db.commit()
        db.refresh(s)
        return to_session_out(db, s, user)

    # 2) còn thiếu câu bắt buộc → giữ collecting
    profile = _require_profile(db, user)
    ai_profile = _ai_profile(profile)
    if await agent_service.missing_questions(ai_profile, answers):
        db.commit()
        db.refresh(s)
        return to_session_out(db, s, user)

    # 3) đủ → chạy agent → pending_review
    ctx = PatientContext(session_id=s.id, profile=ai_profile, answers=answers)
    # TODO(BE, nâng cao): ctx.prior_sessions_summary = tóm tắt phiên approved trước (memory)
    result = await agent_service.run_screening(ctx)
    s.trace_id = result.trace_id
    if result.status == "red_flag":
        s.status = "red_flag"
        s.red_flags = result.red_flag.model_dump(mode="json") if result.red_flag else None
    else:
        s.status = "pending_review"
        s.risk_assessment = result.risk_assessment.model_dump(mode="json") if result.risk_assessment else None
        s.draft_plan = result.draft_plan.model_dump(mode="json") if result.draft_plan else None
    db.commit()
    db.refresh(s)
    return to_session_out(db, s, user)


def get_session_for(db: Session, session_id: str, viewer: User) -> SessionOut:
    s = _get_or_404(db, session_id)
    if viewer.role == "patient" and s.patient_id != viewer.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiên")
    return to_session_out(db, s, viewer)


def list_sessions(
    db: Session, *, patient_id: str | None, status: str | None, page: int, page_size: int
) -> Page[SessionSummary]:
    q = select(ScreeningSession)
    if patient_id:
        q = q.where(ScreeningSession.patient_id == patient_id)
    if status:
        q = q.where(ScreeningSession.status == status)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(
        q.order_by(ScreeningSession.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return Page(items=[to_summary(db, r) for r in rows], total=total, page=page, page_size=page_size)


def patient_detail(db: Session, patient_id: str) -> dict:
    user = db.get(User, patient_id)
    if not user or user.role != "patient":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy bệnh nhân")
    profile = db.get(PatientProfile, patient_id)
    sessions = db.scalars(
        select(ScreeningSession)
        .where(ScreeningSession.patient_id == patient_id)
        .order_by(ScreeningSession.created_at.desc())
    ).all()
    return {
        "user": UserOut.model_validate(user),
        "profile": PatientProfileOut.model_validate(profile) if profile else None,
        "sessions": [to_summary(db, s) for s in sessions],
    }
