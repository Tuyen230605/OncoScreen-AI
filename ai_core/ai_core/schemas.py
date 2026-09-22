"""★ CONTRACT — Pydantic schemas dùng chung giữa AI Core và Backend.

Mọi thay đổi ở file này là thay đổi contract → PR `contract/*`, cập nhật
docs/protocols/AI_CORE_CONTRACT.md và frontend/src/types/api.ts.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# --------------------------------------------------------------------------- enums


class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class CancerType(str, Enum):
    breast = "breast"
    cervical = "cervical"
    colorectal = "colorectal"
    liver = "liver"
    lung = "lung"
    prostate = "prostate"
    other = "other"


class RiskLevel(str, Enum):
    average = "average"
    elevated = "elevated"
    high = "high"


class SessionStatus(str, Enum):
    collecting = "collecting"
    red_flag = "red_flag"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    completed = "completed"


class QuestionType(str, Enum):
    single_choice = "single_choice"
    multi_choice = "multi_choice"
    number = "number"
    boolean = "boolean"
    text = "text"


class RedFlagSeverity(str, Enum):
    urgent = "urgent"  # đi khám ngay
    soon = "soon"  # khám trong vài tuần


# --------------------------------------------------------------------------- input


class PatientProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    age: int = Field(ge=0, le=120)
    gender: Gender
    genetics_history: list[str] = Field(default_factory=list, description="mã tiền sử gia đình, xem questionnaire.json")
    lifestyle: dict[str, Any] = Field(default_factory=dict)
    lifestyle_score: float | None = None


class Answer(BaseModel):
    question_id: str = Field(min_length=1)
    value: Any


class PatientContext(BaseModel):
    session_id: str
    profile: PatientProfile
    answers: list[Answer] = Field(default_factory=list)
    prior_sessions_summary: str | None = Field(default=None, description="memory: tóm tắt các phiên trước (nâng cao)")


# --------------------------------------------------------------------------- questionnaire


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    type: QuestionType
    options: list[str] | None = None
    required: bool = True
    depends_on: str | None = Field(
        default=None, description='điều kiện hiển thị, dạng "question_id=value" (vd. "smoking=true")'
    )


class Questionnaire(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str
    questions: list[Question] = Field(min_length=1)


# --------------------------------------------------------------------------- red flag


class RedFlag(BaseModel):
    code: str
    symptom: str
    severity: RedFlagSeverity
    advice: str


class RedFlagResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detected: bool
    flags: list[RedFlag] = Field(default_factory=list)
    message: str | None = None

    @model_validator(mode="after")
    def _validate_consistency(self) -> RedFlagResult:
        if self.detected and (not self.flags or not self.message):
            raise ValueError("detected red-flag results require flags and message")
        if not self.detected and self.flags:
            raise ValueError("non-detected red-flag results cannot contain flags")
        return self


# --------------------------------------------------------------------------- output


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doc_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    section: str | None = None
    excerpt: str = Field(min_length=1)
    url: str | None = None


class RiskFactor(BaseModel):
    cancer_type: CancerType
    level: RiskLevel
    reasons: list[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    overall_summary: str
    factors: list[RiskFactor] = Field(default_factory=list)


class PlanItem(BaseModel):
    cancer_type: CancerType
    method: str = Field(description="vd. Nhũ ảnh (mammography)")
    start_age: int | None = None
    interval_months: int = Field(gt=0)
    next_due: date
    rationale: str
    sources: list[Source] = Field(min_length=1, description="bắt buộc ≥1 nguồn — guardrail S2")
    priority: int = Field(default=1, ge=1, le=5, description="1 = ưu tiên cao nhất")


class ScreeningPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[PlanItem] = Field(min_length=1)
    general_advice: str = ""
    generated_at: datetime
    model: str = Field(description="tên model/agent đã sinh plan, vd. claude-opus-5 | mock")


class ScreeningResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["pending_review", "red_flag"]
    risk_assessment: RiskAssessment | None = None
    draft_plan: ScreeningPlan | None = None
    red_flag: RedFlagResult | None = None
    disclaimer: str
    trace_id: str

    @model_validator(mode="after")
    def _validate_status_payload(self) -> ScreeningResult:
        if not self.disclaimer.strip():
            raise ValueError("disclaimer must not be empty")
        if not self.trace_id.strip():
            raise ValueError("trace_id must not be empty")
        if self.status == "red_flag":
            if self.draft_plan is not None or self.risk_assessment is not None:
                raise ValueError("red_flag results cannot contain risk_assessment or draft_plan")
            if self.red_flag is None or not self.red_flag.detected:
                raise ValueError("red_flag results require red_flag.detected=true")
        else:
            if self.draft_plan is None or self.risk_assessment is None:
                raise ValueError("pending_review results require risk_assessment and draft_plan")
            if self.red_flag is not None:
                raise ValueError("pending_review results cannot contain red_flag")
        return self


class EducationContent(BaseModel):
    cancer_type: CancerType
    title: str
    warning_signs: list[str] = Field(default_factory=list)
    prevention_tips: list[str] = Field(default_factory=list)
    body_md: str = ""
    sources: list[Source] = Field(default_factory=list)
