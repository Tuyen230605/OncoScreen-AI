from __future__ import annotations

from sqlalchemy import JSON, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._common import Timestamps


class PatientProfile(Timestamps, Base):
    __tablename__ = "patient_profiles"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(16), nullable=False)
    genetics_history: Mapped[list] = mapped_column(JSON, default=list)
    lifestyle: Mapped[dict] = mapped_column(JSON, default=dict)
    lifestyle_score: Mapped[float | None] = mapped_column(Float, nullable=True)
