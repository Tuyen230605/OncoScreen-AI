from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._common import Timestamps, UUIDPk


class Reminder(UUIDPk, Timestamps, Base):
    __tablename__ = "reminders"

    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("screening_sessions.id"), nullable=False)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    cancer_type: Mapped[str] = mapped_column(String(32), nullable=False)
    method: Mapped[str] = mapped_column(String(255), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="scheduled")  # scheduled | due | done | skipped
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
