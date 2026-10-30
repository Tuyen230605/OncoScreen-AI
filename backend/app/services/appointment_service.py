"""Đặt lịch khám (mô phỏng): bệnh nhân tạo yêu cầu, bác sĩ xác nhận. Mỗi thay đổi ghi vào hồ sơ xuyên suốt."""

from __future__ import annotations

from datetime import date

from ai_core.schemas import NavigatorReply
from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import Appointment, AuditLog, Consultation, Encounter, User
from app.schemas.appointment import AppointmentIn, AppointmentOut
from app.schemas.common import Page
from app.services import agent_service, record_service

MAX_OPEN = 3
OPEN_STATUSES = ("requested", "confirmed")


def services_by_code() -> dict[str, dict]:
    return {s["code"]: s for s in agent_service.list_services()}


def to_out(db: Session, a: Appointment) -> AppointmentOut:
    patient = db.get(User, a.patient_id)
    service = services_by_code().get(a.service_code, {})
    encounter_id = db.scalar(select(Encounter.id).where(Encounter.appointment_id == a.id))
    return AppointmentOut(
        id=a.id,
        patient_id=a.patient_id,
        patient_name=patient.full_name if patient else "?",
        consultation_id=a.consultation_id,
        service_code=a.service_code,
        service_name=service.get("name", a.service_code),
        preferred_date=a.preferred_date,
        scheduled_date=a.scheduled_date,
        reason=a.reason,
        priority=a.priority,
        status=a.status,
        encounter_id=encounter_id,
        created_at=a.created_at,
    )


def _get_or_404(db: Session, appointment_id: str) -> Appointment:
    a = db.get(Appointment, appointment_id)
    if not a:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy lịch hẹn")
    return a


def create(db: Session, user: User, body: AppointmentIn) -> AppointmentOut:
    service = services_by_code().get(body.service_code)
    if not service:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dịch vụ không tồn tại")
    if body.preferred_date < date.today():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ngày mong muốn không được ở quá khứ")
    open_count = db.scalar(
        select(func.count())
        .select_from(Appointment)
        .where(Appointment.patient_id == user.id, Appointment.status.in_(OPEN_STATUSES))
    )
    if (open_count or 0) >= MAX_OPEN:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Bạn đang có {MAX_OPEN} lịch hẹn chưa hoàn tất")
    consult = None
    if body.consultation_id:
        consult = db.get(Consultation, body.consultation_id)
        if not consult or consult.patient_id != user.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy phiên tư vấn")
    urgent = bool(consult and consult.red_flag) or body.service_code == "oncology_priority"
    reason = (body.reason or "").strip() or None
    if reason is None and consult and consult.last_reply:
        hint = NavigatorReply.model_validate(consult.last_reply).booking_hint
        reason = hint.reason if hint else None
    a = Appointment(
        patient_id=user.id,
        consultation_id=consult.id if consult else None,
        service_code=body.service_code,
        preferred_date=body.preferred_date,
        reason=reason,
        priority="urgent" if urgent else "routine",
        status="requested",
    )
    db.add(a)
    db.flush()
    record_service.add_event(
        db,
        user.id,
        "appointment.requested",
        f"Đặt lịch {service['name']} (mong muốn {body.preferred_date:%d/%m/%Y})"
        + (" — ưu tiên" if urgent else "")
        + (f". Lý do: {reason}" if reason else "."),
        data={"service_code": body.service_code, "priority": a.priority},
        ref_type="appointment",
        ref_id=a.id,
        actor_id=user.id,
    )
    db.add(AuditLog(actor_id=user.id, action="appointment.create", entity="appointment", entity_id=a.id))
    db.commit()
    db.refresh(a)
    return to_out(db, a)


def escalate_for_red_flag(db: Session, consult: Consultation) -> None:
    """R2: dấu hiệu cảnh báo ghi nhận SAU khi đã đặt lịch từ phiên này → nâng các lịch còn mở lên khẩn."""
    if not consult.red_flag or not consult.patient_id:
        return
    rows = db.scalars(
        select(Appointment).where(
            Appointment.consultation_id == consult.id,
            Appointment.status.in_(OPEN_STATUSES),
            Appointment.priority != "urgent",
        )
    ).all()
    for a in rows:
        a.priority = "urgent"
        record_service.add_event(
            db,
            a.patient_id,
            "appointment.escalated",
            "Lịch hẹn được chuyển sang ưu tiên khám sớm do ghi nhận dấu hiệu cần lưu ý khi tư vấn.",
            data={"service_code": a.service_code, "priority": a.priority},
            ref_type="appointment",
            ref_id=a.id,
            actor_id=consult.patient_id,
        )
        db.add(
            AuditLog(
                actor_id=consult.patient_id,
                action="appointment.escalate",
                entity="appointment",
                entity_id=a.id,
                before={"priority": "routine"},
                after={"priority": "urgent"},
            )
        )


def list_mine(db: Session, user: User) -> list[AppointmentOut]:
    rows = db.scalars(
        select(Appointment).where(Appointment.patient_id == user.id).order_by(Appointment.created_at.desc())
    ).all()
    return [to_out(db, a) for a in rows]


def cancel(db: Session, user: User, appointment_id: str) -> AppointmentOut:
    a = _get_or_404(db, appointment_id)
    if a.patient_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy lịch hẹn")
    if a.status not in OPEN_STATUSES:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Lịch hẹn đang ở trạng thái {a.status}")
    if db.scalar(select(Encounter.id).where(Encounter.appointment_id == a.id)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Bác sĩ đã bắt đầu khám, không thể huỷ lịch hẹn này")
    a.status = "cancelled"
    record_service.add_event(
        db,
        user.id,
        "appointment.cancelled",
        "Bệnh nhân huỷ lịch hẹn.",
        ref_type="appointment",
        ref_id=a.id,
        actor_id=user.id,
    )
    db.add(AuditLog(actor_id=user.id, action="appointment.cancel", entity="appointment", entity_id=a.id))
    db.commit()
    db.refresh(a)
    return to_out(db, a)


def list_for_doctor(db: Session, status_: str | None, page: int, page_size: int) -> Page[AppointmentOut]:
    q = select(Appointment)
    if status_:
        q = q.where(Appointment.status == status_)
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(
        q.order_by(
            case((Appointment.priority == "urgent", 0), else_=1),
            func.coalesce(Appointment.scheduled_date, Appointment.preferred_date),
            Appointment.created_at,
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page(items=[to_out(db, a) for a in rows], total=total, page=page, page_size=page_size)


def confirm(db: Session, doctor: User, appointment_id: str, scheduled_date: date) -> AppointmentOut:
    a = _get_or_404(db, appointment_id)
    if a.status != "requested":
        raise HTTPException(status.HTTP_409_CONFLICT, f"Lịch hẹn đang ở trạng thái {a.status}")
    if scheduled_date < date.today():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ngày hẹn không được ở quá khứ")
    a.status, a.scheduled_date, a.doctor_id = "confirmed", scheduled_date, doctor.id
    record_service.add_event(
        db,
        a.patient_id,
        "appointment.confirmed",
        f"Lịch hẹn được xác nhận ngày {scheduled_date:%d/%m/%Y} ({doctor.full_name}).",
        ref_type="appointment",
        ref_id=a.id,
        actor_id=doctor.id,
    )
    db.add(AuditLog(actor_id=doctor.id, action="appointment.confirm", entity="appointment", entity_id=a.id))
    db.commit()
    db.refresh(a)
    return to_out(db, a)
