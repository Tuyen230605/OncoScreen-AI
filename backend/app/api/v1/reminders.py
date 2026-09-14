from datetime import date

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.api.deps import DB, Patient
from app.schemas.session import ReminderOut
from app.services import scheduler

router = APIRouter()


class CompleteIn(BaseModel):
    completed_at: date | None = None


@router.get("", response_model=list[ReminderOut])
def my_reminders(user: Patient, db: DB, status_: str | None = Query(None, alias="status")):
    return scheduler.list_for_patient(db, user.id, status_)


@router.post("/{reminder_id}/complete", response_model=ReminderOut)
def complete(reminder_id: str, body: CompleteIn, user: Patient, db: DB):
    return scheduler.complete(db, reminder_id, user, body.completed_at)
