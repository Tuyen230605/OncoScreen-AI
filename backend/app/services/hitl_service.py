"""HITL: bác sĩ approve / reject bản nháp. Approve → final_plan + reminders + audit (R5, S4)."""

from __future__ import annotations

from datetime import UTC, datetime

from ai_core.guardrails.safety import GuardrailViolation, validate_plan
from ai_core.schemas import ScreeningPlan
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import AuditLog, ScreeningSession, User
from app.schemas.session import ReviewIn, SessionOut
from app.services import scheduler
from app.services.session_service import to_session_out


def review(db: Session, session_id: str, doctor: User, body: ReviewIn) -> SessionOut:
    s = db.get(ScreeningSession, session_id)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiên")
    if s.status != "pending_review":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Phiên đang ở trạng thái {s.status}, không thể duyệt")

    s.doctor_id = doctor.id
    s.reviewed_at = datetime.now(UTC)

    if body.action == "reject":
        if not body.note:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Từ chối cần ghi lý do (note)")
        s.status = "rejected"
        s.doctor_note = body.note
        db.add(AuditLog(session_id=s.id, actor_id=doctor.id, action="session.reject", after={"note": body.note}))
        db.commit()
        db.refresh(s)
        return to_session_out(db, s, doctor)

    # approve
    final = body.final_plan or (ScreeningPlan.model_validate(s.draft_plan) if s.draft_plan else None)
    if final is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không có plan để duyệt")
    try:
        validate_plan(final)  # bác sĩ sửa vẫn phải qua guardrail (nguồn, ngôn ngữ)
    except GuardrailViolation as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Plan vi phạm guardrail: {exc}") from exc

    final_json = final.model_dump(mode="json")
    if body.final_plan is not None and final_json != s.draft_plan:
        db.add(AuditLog(session_id=s.id, actor_id=doctor.id, action="plan.edit", before=s.draft_plan, after=final_json))
    s.final_plan = final_json
    s.doctor_note = body.note
    s.status = "approved"
    db.add(AuditLog(session_id=s.id, actor_id=doctor.id, action="session.approve"))
    scheduler.create_reminders_for_plan(db, s, final)
    db.commit()
    db.refresh(s)
    return to_session_out(db, s, doctor)
