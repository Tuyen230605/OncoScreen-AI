"""Reminders + APScheduler tick (mô phỏng nhắc lịch định kỳ)."""

from __future__ import annotations

import logging
from datetime import date

from ai_core.schemas import CancerType, ScreeningPlan
from ai_core.tools.booking import next_due_date
from ai_core.tools.recall_reminder import build_reminder_message
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import AuditLog, Encounter, Reminder, User

log = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


# ------------------------------------------------------------------ CRUD


def create_reminders_for_plan(db: Session, encounter: Encounter, plan: ScreeningPlan) -> list[Reminder]:
    out = []
    for item in plan.items:
        if item.next_due is None:
            continue
        r = Reminder(
            encounter_id=encounter.id,
            patient_id=encounter.patient_id,
            cancer_type=item.cancer_type.value,
            method=item.method,
            due_date=item.next_due,
            status="scheduled",
        )
        db.add(r)
        out.append(r)
    return out


def _next_cycle_due(last_done: date, interval_months: int) -> date | None:
    """Ngày hẹn chu kỳ kế tiếp; None nếu vượt phạm vi lịch (dữ liệu cũ có chu kỳ bất thường) thay vì lỗi 500."""
    try:
        return next_due_date(last_done, interval_months)
    except (OverflowError, ValueError):
        log.warning("scheduler: bỏ qua chu kỳ kế tiếp, interval_months=%s vượt phạm vi lịch", interval_months)
        return None


def list_for_patient(db: Session, patient_id: str, status_: str | None) -> list[Reminder]:
    q = select(Reminder).where(Reminder.patient_id == patient_id)
    if status_:
        q = q.where(Reminder.status == status_)
    return db.scalars(q.order_by(Reminder.due_date)).all()


def list_due(db: Session) -> list[Reminder]:
    return db.scalars(select(Reminder).where(Reminder.status == "due").order_by(Reminder.due_date)).all()


def complete(db: Session, reminder_id: str, user: User, completed_at: date | None) -> Reminder:
    r = db.get(Reminder, reminder_id)
    if not r or r.patient_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy nhắc lịch")
    if r.status == "done":
        return r
    actual_date = completed_at or date.today()
    if actual_date > date.today():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ngày đã tầm soát không được ở tương lai")
    r.status = "done"
    r.completed_at = actual_date
    db.add(AuditLog(actor_id=user.id, action="reminder.complete", entity="reminder", entity_id=r.id))
    from app.services import record_service

    record_service.add_event(
        db,
        r.patient_id,
        "reminder.done",
        f"Bệnh nhân xác nhận đã thực hiện {r.method} ngày {actual_date:%d/%m/%Y}.",
        data={"cancer_types": [r.cancer_type], "completed_at": actual_date.isoformat()},
        ref_type="reminder",
        ref_id=r.id,
        actor_id=user.id,
    )
    encounter = db.get(Encounter, r.encounter_id)
    if encounter and encounter.final_plan:
        plan = ScreeningPlan.model_validate(encounter.final_plan)
        matching = [item for item in plan.items if item.cancer_type.value == r.cancer_type and item.method == r.method]
        due = _next_cycle_due(actual_date, matching[0].interval_months) if len(matching) == 1 else None
        if due is not None:
            exists = db.scalar(
                select(Reminder).where(
                    Reminder.encounter_id == r.encounter_id,
                    Reminder.cancer_type == r.cancer_type,
                    Reminder.method == r.method,
                    Reminder.due_date == due,
                    Reminder.id != r.id,
                )
            )
            if not exists:
                db.add(
                    Reminder(
                        encounter_id=r.encounter_id,
                        patient_id=r.patient_id,
                        cancer_type=r.cancer_type,
                        method=r.method,
                        due_date=due,
                        status="scheduled",
                    )
                )
                db.add(
                    AuditLog(
                        actor_id=user.id,
                        action="reminder.next_scheduled",
                        entity="reminder",
                        entity_id=r.id,
                        after={"due_date": due.isoformat(), "cancer_type": r.cancer_type},
                    )
                )
    db.commit()
    db.refresh(r)
    return r


# ------------------------------------------------------------------ tick


def tick() -> int:
    """Chuyển reminders scheduled đã đến hạn → due, sinh message. Trả số reminder đã cập nhật."""
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(Reminder).where(Reminder.status == "scheduled", Reminder.due_date <= date.today())
        ).all()
        for r in rows:
            patient = db.get(User, r.patient_id)
            r.status = "due"
            r.message = build_reminder_message(
                CancerType(r.cancer_type), r.method, r.due_date, patient.full_name if patient else None
            )
        db.commit()
        if rows:
            log.info("scheduler: %d reminder(s) → due", len(rows))
        return len(rows)
    finally:
        db.close()


def start() -> None:
    global _scheduler
    if _scheduler:
        return
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(tick, "interval", seconds=settings.reminder_tick_seconds, id="reminder_tick")
    _scheduler.start()


def shutdown() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
