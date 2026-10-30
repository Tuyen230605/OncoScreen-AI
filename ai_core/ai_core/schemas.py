"""★ CONTRACT — Pydantic schemas dùng chung giữa AI Core và Backend.

Mọi thay đổi ở file này là thay đổi contract → PR `contract/*`, cập nhật
docs/protocols/AI_CORE_CONTRACT.md và frontend/src/types/api.ts.

Hai agent dùng chung một lõi:
- Navigator (người dùng, ẩn danh): giải đáp + gợi ý tầm soát theo nhóm + điều hướng đặt lịch.
- Clinical Copilot (bác sĩ): tóm tắt hồ sơ xuyên suốt + gợi ý theo guideline + bản nháp kế hoạch để bác sĩ duyệt.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

TraceEvent = dict[str, str | int | float | bool]

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


class QuestionType(str, Enum):
    single_choice = "single_choice"
    multi_choice = "multi_choice"
    number = "number"
    boolean = "boolean"
    text = "text"


class RedFlagSeverity(str, Enum):
    urgent = "urgent"  # đi khám ngay
    soon = "soon"  # khám trong vài tuần


class NextAction(str, Enum):
    """Điều hướng sau mỗi lượt Navigator."""

    continue_chat = "continue_chat"  # tiếp tục hỏi đáp / còn thiếu thông tin
    suggest_booking = "suggest_booking"  # có mốc tầm soát phù hợp hoặc nguy cơ tăng → gợi ý tạo tài khoản & đặt lịch
    urgent_care = "urgent_care"  # có dấu hiệu cảnh báo → khám sớm, ngắt tư vấn tầm soát


class BookingPriority(str, Enum):
    routine = "routine"
    urgent = "urgent"


# --------------------------------------------------------------------------- hồ sơ


class PatientProfile(BaseModel):
    """Hồ sơ của tài khoản đã đăng ký (backend lưu ở patient_profiles)."""

    model_config = ConfigDict(extra="forbid")

    age: int = Field(ge=0, le=120)
    gender: Gender
    genetics_history: list[str] = Field(
        default_factory=list, description="mã tiền sử gia đình, vd. breast_cancer_mother"
    )
    lifestyle: dict[str, Any] = Field(default_factory=dict)
    lifestyle_score: float | None = None


class IntakeProfile(BaseModel):
    """Thông tin sàng lọc Navigator thu thập dần trong hội thoại ẩn danh; mọi trường có thể chưa biết."""

    model_config = ConfigDict(extra="forbid")

    age: int | None = Field(default=None, ge=0, le=120)
    gender: Gender | None = None
    family_history: list[CancerType] = Field(default_factory=list)
    personal_cancer_history: bool | None = None
    smoking: bool | None = None
    pack_years: float | None = Field(default=None, ge=0)
    hepatitis_b_or_c: bool | None = None
    cirrhosis: bool | None = None
    hpv_vaccinated: bool | None = None
    symptom_codes: list[str] = Field(default_factory=list, description="mã red-flag đã ghi nhận")


class Answer(BaseModel):
    question_id: str = Field(min_length=1)
    value: Any


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


# --------------------------------------------------------------------------- nguồn & kế hoạch


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


class ScreeningSuggestion(BaseModel):
    """Mốc tầm soát áp dụng cho NHÓM người dùng (tuổi/giới/yếu tố nguy cơ) theo guideline — mang tính giáo dục,
    không phải chỉ định cá nhân. Sinh bởi bộ luật xác định (eligibility engine), không phải LLM."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str
    cancer_type: CancerType
    method: str
    start_age: int | None = None
    interval_months: int | None = Field(default=None, gt=0, description="null = guideline không nêu chu kỳ cố định")
    applies_because: str
    note: str | None = None
    elevated_risk: bool = False
    sources: list[Source] = Field(min_length=1)


class PlanItem(BaseModel):
    cancer_type: CancerType
    method: str = Field(description="vd. Nhũ ảnh (mammography)")
    start_age: int | None = None
    interval_months: int = Field(gt=0)
    next_due: date | None = None
    rationale: str
    sources: list[Source] = Field(min_length=1, description="bắt buộc ≥1 nguồn — guardrail S2")
    priority: int = Field(default=1, ge=1, le=5, description="1 = ưu tiên cao nhất")


class ScreeningPlan(BaseModel):
    """Kế hoạch theo dõi cá nhân. AI chỉ soạn nháp; chỉ có hiệu lực khi bác sĩ duyệt (S4)."""

    model_config = ConfigDict(extra="forbid")

    items: list[PlanItem] = Field(min_length=1)
    general_advice: str = ""
    generated_at: datetime
    model: str = Field(description="tên model/agent đã sinh plan, vd. openai/gpt-5.4-mini | mock | doctor")


# --------------------------------------------------------------------------- Navigator (người dùng)


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class BookingHint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    priority: BookingPriority
    service_codes: list[str] = Field(min_length=1, description="mã dịch vụ trong data/services.json")
    reason: str


class NavigatorReply(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reply: str = Field(min_length=1)
    sources: list[Source] = Field(default_factory=list)
    intake: IntakeProfile
    missing_info: list[str] = Field(default_factory=list, description="trường cần hỏi thêm: age, gender, pack_years…")
    suggestions: list[ScreeningSuggestion] = Field(default_factory=list)
    risk_factors: list[RiskFactor] = Field(default_factory=list)
    red_flag: RedFlagResult
    next_action: NextAction
    booking_hint: BookingHint | None = None
    insufficient_evidence: bool = False
    disclaimer: str
    trace_id: str
    trace_events: list[TraceEvent] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_triage(self) -> NavigatorReply:
        if not self.disclaimer.strip() or not self.trace_id.strip():
            raise ValueError("disclaimer and trace_id must not be empty")
        if self.red_flag.detected:
            if self.next_action != NextAction.urgent_care:
                raise ValueError("red-flag replies must route to urgent_care")
            if self.suggestions:
                raise ValueError("red-flag replies cannot contain screening suggestions")
            if self.booking_hint is None or self.booking_hint.priority != BookingPriority.urgent:
                raise ValueError("red-flag replies require an urgent booking_hint")
        elif self.next_action == NextAction.urgent_care:
            raise ValueError("urgent_care requires a detected red flag")
        if self.next_action != NextAction.continue_chat and self.booking_hint is None:
            raise ValueError("booking routes require booking_hint")
        return self


# --------------------------------------------------------------------------- Clinical Copilot (bác sĩ)


class RecordEvent(BaseModel):
    """Một mốc trong hồ sơ xuyên suốt (timeline) do backend tổng hợp."""

    model_config = ConfigDict(extra="forbid")

    id: str
    at: datetime
    kind: str = Field(description="consult.summary | red_flag | appointment.* | encounter.finalized | reminder.* …")
    summary: str
    data: dict[str, Any] = Field(default_factory=dict)


class PatientRecord(BaseModel):
    """Toàn bộ dữ liệu một bệnh nhân từ lần tư vấn đầu tới hiện tại — đầu vào cho Copilot."""

    model_config = ConfigDict(extra="forbid")

    patient_id: str
    full_name: str | None = None
    profile: PatientProfile | None = None
    intake: IntakeProfile | None = None
    reason_for_visit: str | None = None
    events: list[RecordEvent] = Field(default_factory=list)


class BriefFact(BaseModel):
    text: str
    event_ids: list[str] = Field(min_length=1, description="truy vết về RecordEvent.id — chống bịa")


class ClinicalBrief(BaseModel):
    """Tóm tắt trước khám cho bác sĩ. Công cụ hỗ trợ quyết định: không chẩn đoán, không diễn giải kết quả."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    key_facts: list[BriefFact] = Field(default_factory=list)
    red_flags: list[RedFlag] = Field(default_factory=list)
    risk_factors: list[RiskFactor] = Field(default_factory=list)
    guideline_suggestions: list[ScreeningSuggestion] = Field(default_factory=list)
    questions_to_clarify: list[str] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    draft_plan: ScreeningPlan | None = None
    disclaimer: str
    generated_at: datetime
    model: str
    trace_id: str
    trace_events: list[TraceEvent] = Field(default_factory=list)


# --------------------------------------------------------------------------- hỏi đáp & giáo dục


class EducationContent(BaseModel):
    cancer_type: CancerType
    title: str
    warning_signs: list[str] = Field(default_factory=list)
    prevention_tips: list[str] = Field(default_factory=list)
    body_md: str = ""
    sources: list[Source] = Field(default_factory=list)


class QuestionAnswer(BaseModel):
    answer: str
    sources: list[Source] = Field(default_factory=list)
    disclaimer: str
    trace_id: str
    insufficient_evidence: bool = False
    trace_events: list[TraceEvent] = Field(default_factory=list)
