from __future__ import annotations

from datetime import datetime
from typing import Any

from ai_core.schemas import Gender
from pydantic import BaseModel, Field


class PatientProfileIn(BaseModel):
    age: int = Field(ge=0, le=120)
    gender: Gender
    genetics_history: list[str] = Field(default_factory=list)
    lifestyle: dict[str, Any] = Field(default_factory=dict)


class PatientProfileOut(PatientProfileIn):
    user_id: str
    lifestyle_score: float | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}
