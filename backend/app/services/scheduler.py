"""Reminders + APScheduler tick (mô phỏng nhắc lịch định kỳ)."""

from __future__ import annotations

import logging
from datetime import date

from ai_core.schemas import CancerType, ScreeningPlan
from ai_core.tools.recall_reminder import build_reminder_message
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import AuditLog, Reminder, ScreeningSession, User

log = logging.getLogger(__name__)
_scheduler: BackgroundScheduler | None = None


# ------------------------------------------------------------------ CRUD


def create_reminders_for_plan(db: Session, session: ScreeningSession, plan: ScreeningPlan) -> list[Reminder]:
    out = []
    for item in plan.items:
        r = Reminder(
            session_id=session.id,
            patient_id=session.patient_id,
            cancer_type=item.cancer_type.value,
            method=item.method,
            due_date=item.next_due,
            status="scheduled",
        )
        db.add(r)
        out.append(r)
    return out


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
    r.status = "done"
    r.completed_at = completed_at or date.today()
    db.add(AuditLog(session_id=r.session_id, actor_id=user.id, action="reminder.complete", after={"id": r.id}))
    # TODO(BE, nâng cao): tạo reminder kế tiếp = completed_at + interval_months (lấy từ final_plan)
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
