from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._common import Timestamps, UUIDPk


class ScreeningSession(UUIDPk, Timestamps, Base):
    """1 phiên tầm soát. Các cột JSON lưu nguyên `model_dump(mode="json")` của ai_core.schemas."""

    __tablename__ = "screening_sessions"

    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    doctor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="collecting")

    questionnaire: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    answers: Mapped[list] = mapped_column(JSON, default=list)
    red_flags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    risk_assessment: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    draft_plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    final_plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    doctor_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
