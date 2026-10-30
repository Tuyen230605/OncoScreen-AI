from __future__ import annotations

from datetime import datetime
from typing import Literal

from ai_core.schemas import ChatTurn, ClinicalBrief, ScreeningPlan
from pydantic import BaseModel, Field, field_validator

from app.schemas.appointment import ReminderOut
from app.schemas.auth import UserOut


class EncounterOut(BaseModel):
    """Serializer PHẢI áp dụng quy tắc lộ dữ liệu theo role — xem services/encounter_service.to_out()."""

    id: str
    appointment_id: str
    patient_id: str
    patient_name: str
    doctor: UserOut | None = None
    status: Literal["in_progress", "finalized"]
    brief: ClinicalBrief | None = None
    draft_plan: ScreeningPlan | None = None
    final_plan: ScreeningPlan | None = None
    clinical_notes: str | None = None
    conclusion: str | None = None
    finalized_at: datetime | None = None
    created_at: datetime
    reminders: list[ReminderOut] = Field(default_factory=list)
    disclaimer: str


MAX_INTERVAL_MONTHS = 120  # 10 năm — chu kỳ dài nhất trong guideline; chặn lỗi nhập liệu & ngày hẹn vượt lịch


class FinalizeEncounterIn(BaseModel):
    conclusion: str = Field(min_length=1, max_length=4000)
    clinical_notes: str | None = Field(default=None, max_length=8000)
    final_plan: ScreeningPlan | None = None
    use_draft: bool = True

    @field_validator("conclusion")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Kết luận không được để trống")
        return value.strip()

    @field_validator("final_plan")
    @classmethod
    def interval_in_range(cls, plan: ScreeningPlan | None) -> ScreeningPlan | None:
        for i, item in enumerate(plan.items if plan else []):
            if item.interval_months > MAX_INTERVAL_MONTHS:
                raise ValueError(f"items[{i}].interval_months không được vượt quá {MAX_INTERVAL_MONTHS} tháng")
        return plan


class CopilotAskIn(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=8)
