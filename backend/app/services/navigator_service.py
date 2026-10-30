"""Navigator: phiên tư vấn ẩn danh (token) → gắn vào tài khoản khi người dùng đăng ký/đăng nhập."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from time import monotonic

from ai_core.api import genetics_codes_from_intake, intake_from_profile
from ai_core.schemas import ChatTurn, IntakeProfile, NavigatorReply
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import AuditLog, Consultation, PatientProfile, User
from app.models._common import utcnow
from app.schemas.navigator import ConsultationCreated, ConsultationOut, NavigatorMessageIn
from app.services import agent_service, appointment_service, record_service
from app.services.record_service import ai_profile

MAX_TURNS = 40


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def token_matches(c: Consultation, token: str) -> bool:
    return hmac.compare_digest(_hash(token), c.token_hash)


def to_out(c: Consultation) -> ConsultationOut:
    return ConsultationOut(
        id=c.id,
        linked=c.patient_id is not None,
        intake=IntakeProfile.model_validate(c.intake or {}),
        messages=c.messages or [],
        last_reply=c.last_reply,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


def create(db: Session, user: User | None) -> ConsultationCreated:
    token = secrets.token_urlsafe(24)
    intake = IntakeProfile()
    patient_id = None
    if user is not None and user.role == "patient":
        patient_id = user.id
        profile = ai_profile(db.get(PatientProfile, user.id))
        if profile:
            intake = intake_from_profile(profile)
    c = Consultation(patient_id=patient_id, token_hash=_hash(token), intake=intake.model_dump(mode="json"), messages=[])
    db.add(c)
    db.flush()
    db.add(AuditLog(actor_id=user.id if user else None, action="consult.create", entity="consultation", entity_id=c.id))
    db.commit()
    db.refresh(c)
    return ConsultationCreated(access_token=token, consultation=to_out(c))


def authorize(db: Session, consult_id: str, token: str | None, user: User | None) -> Consultation:
    c = db.get(Consultation, consult_id)
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiên tư vấn")
    if c.patient_id:
        if user is None or user.id != c.patient_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiên tư vấn")
        return c
    if not token or not token_matches(c, token):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Thiếu hoặc sai mã phiên tư vấn")
    return c


async def post_message(db: Session, c: Consultation, body: NavigatorMessageIn) -> ConsultationOut:
    messages = list(c.messages or [])
    if len(messages) >= MAX_TURNS * 2:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Phiên tư vấn đã quá dài; vui lòng bắt đầu phiên mới")
    history = [ChatTurn(role=m["role"], content=m["content"][:4000]) for m in messages[-8:]]
    started = monotonic()
    reply = await agent_service.navigate(
        body.message, body.answers, IntakeProfile.model_validate(c.intake or {}), history
    )
    agent_service.record_run(
        db,
        "navigator",
        trace_id=reply.trace_id,
        events=reply.trace_events,
        started=started,
        patient_id=c.patient_id,
        consultation_id=c.id,
        red_flag=reply.red_flag.detected,
        next_action=reply.next_action.value,
        insufficient_evidence=reply.insufficient_evidence,
    )
    now = utcnow().isoformat()
    user_text = (body.message or "").strip() or f"(Đã trả lời bảng hỏi nhanh: {len(body.answers)} câu)"
    messages += [
        {"role": "user", "content": user_text, "at": now},
        {"role": "assistant", "content": reply.reply, "at": now},
    ]
    public_reply: NavigatorReply = reply.model_copy(update={"trace_events": []})
    c.messages = messages
    c.intake = reply.intake.model_dump(mode="json")
    c.last_reply = public_reply.model_dump(mode="json")
    c.red_flag = c.red_flag or reply.red_flag.detected
    c.next_action = reply.next_action.value
    record_service.sync_consultation_events(db, c)
    appointment_service.escalate_for_red_flag(db, c)
    db.commit()
    db.refresh(c)
    return to_out(c)


def link(db: Session, c: Consultation, user: User) -> None:
    """Gắn phiên vào tài khoản; điền sẵn hồ sơ khi đủ tuổi + giới; ghi mốc vào hồ sơ xuyên suốt."""
    c.patient_id = user.id
    intake = IntakeProfile.model_validate(c.intake or {})
    if intake.age is not None and intake.gender is not None and not db.get(PatientProfile, user.id):
        lifestyle = {
            k: v
            for k, v in {
                "smoking": intake.smoking,
                "pack_years": intake.pack_years,
                "hepatitis_b_or_c": intake.hepatitis_b_or_c,
                "cirrhosis": intake.cirrhosis,
            }.items()
            if v is not None
        }
        db.add(
            PatientProfile(
                user_id=user.id,
                age=intake.age,
                gender=intake.gender.value,
                genetics_history=genetics_codes_from_intake(intake),
                lifestyle=lifestyle,
            )
        )
        record_service.add_event(
            db, user.id, "profile.updated", "Hồ sơ được điền sẵn từ phiên tư vấn.", ref_type="consultation", ref_id=c.id
        )
    record_service.sync_consultation_events(db, c)
    db.add(AuditLog(actor_id=user.id, action="consult.link", entity="consultation", entity_id=c.id))


def claim(db: Session, consult_id: str, token: str | None, user: User) -> ConsultationOut:
    c = db.get(Consultation, consult_id)
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiên tư vấn")
    if c.patient_id == user.id:
        return to_out(c)
    if c.patient_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Phiên tư vấn đã thuộc tài khoản khác")
    if not token or not token_matches(c, token):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Thiếu hoặc sai mã phiên tư vấn")
    link(db, c, user)
    db.commit()
    db.refresh(c)
    return to_out(c)
