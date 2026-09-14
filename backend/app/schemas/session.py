from __future__ import annotations

from datetime import date, datetime
from typing import Generic, Literal, TypeVar

from ai_core.schemas import Answer, Questionnaire, RedFlagResult, RiskAssessment, ScreeningPlan
from pydantic import BaseModel, Field

from app.schemas.auth import UserOut

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class AnswersIn(BaseModel):
    answers: list[Answer]


class ReviewIn(BaseModel):
    action: Literal["approve", "reject"]
    final_plan: ScreeningPlan | None = None
    note: str | None = None


class ReminderOut(BaseModel):
    id: str
    session_id: str
    patient_id: str
    cancer_type: str
    method: str
    due_date: date
    status: str
    completed_at: date | None = None
    message: str | None = None

    model_config = {"from_attributes": True}


class SessionSummary(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    status: str
    created_at: datetime
    updated_at: datetime
    has_red_flag: bool


class SessionOut(SessionSummary):
    """Serializer PHẢI áp dụng quy tắc lộ dữ liệu theo role — xem services/session_service.to_session_out()."""

    questionnaire: Questionnaire | None = None
    answers: list[Answer] = Field(default_factory=list)
    red_flag: RedFlagResult | None = None
    risk_assessment: RiskAssessment | None = None
    draft_plan: ScreeningPlan | None = None
    final_plan: ScreeningPlan | None = None
    doctor_note: str | None = None
    reviewed_by: UserOut | None = None
    reviewed_at: datetime | None = None
    disclaimer: str
    reminders: list[ReminderOut] = Field(default_factory=list)
