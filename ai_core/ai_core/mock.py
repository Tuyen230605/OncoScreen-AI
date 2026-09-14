"""MockAgent — trả dữ liệu giả HỢP LỆ theo contract để backend/frontend dev không cần LLM.

Red-flag ở mock là THẬT (rule-based, dùng chung detector) để FE test được màn cảnh báo.
TODO(Tuyền): bổ sung case khi contract đổi.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta

from ai_core.guardrails.disclaimer import DISCLAIMER_VI
from ai_core.schemas import (
    Answer,
    CancerType,
    EducationContent,
    PatientContext,
    PatientProfile,
    PlanItem,
    Questionnaire,
    RedFlagResult,
    RiskAssessment,
    RiskFactor,
    RiskLevel,
    ScreeningPlan,
    ScreeningResult,
    Source,
)
from ai_core.tools.questionnaire import build_questionnaire, missing_required
from ai_core.tools.red_flag_detector import detect_red_flags

_SRC_BREAST = Source(
    doc_id="breast_uspstf_2024",
    title="USPSTF 2024 — Breast Cancer Screening",
    section="Recommendation",
    excerpt="Biennial screening mammography for women aged 40 to 74 years.",
    url="https://www.uspreventiveservicestaskforce.org/",
)
_SRC_LUNG = Source(
    doc_id="lung_uspstf_2021",
    title="USPSTF 2021 — Lung Cancer Screening",
    section="Recommendation",
    excerpt="Annual LDCT for adults 50–80 with a 20 pack-year history who currently smoke or quit within 15 years.",
)
_SRC_CRC = Source(
    doc_id="colorectal_uspstf_2021",
    title="USPSTF 2021 — Colorectal Cancer Screening",
    excerpt="Screening for colorectal cancer in all adults aged 45 to 75 years.",
)
_SRC_CERV = Source(
    doc_id="cervical_who_2021",
    title="WHO 2021 — Cervical Cancer Screening",
    excerpt="HPV DNA testing every 5 to 10 years starting at age 30 for the general population.",
)


class MockAgent:
    name = "mock"

    def get_questionnaire(self, profile: PatientProfile) -> Questionnaire:
        return build_questionnaire(profile)

    def check_red_flags(self, answers: list[Answer]) -> RedFlagResult:
        return detect_red_flags(answers)

    def missing_questions(self, profile: PatientProfile, answers: list[Answer]) -> list[str]:
        return missing_required(profile, answers)

    def run_screening(self, ctx: PatientContext) -> ScreeningResult:
        trace_id = f"mock-{uuid.uuid4().hex[:8]}"
        rf = self.check_red_flags(ctx.answers)
        if rf.detected:
            return ScreeningResult(status="red_flag", red_flag=rf, disclaimer=DISCLAIMER_VI, trace_id=trace_id)

        p = ctx.profile
        today = date.today()
        items: list[PlanItem] = []
        factors: list[RiskFactor] = []

        family_breast = any("breast" in g for g in p.genetics_history)
        if p.gender.value == "female" and p.age >= 40:
            level = RiskLevel.elevated if family_breast else RiskLevel.average
            factors.append(
                RiskFactor(
                    cancer_type=CancerType.breast,
                    level=level,
                    reasons=["Nữ ≥ 40 tuổi"] + (["Tiền sử gia đình ung thư vú"] if family_breast else []),
                )
            )
            items.append(
                PlanItem(
                    cancer_type=CancerType.breast,
                    method="Nhũ ảnh (mammography)",
                    start_age=40,
                    interval_months=12 if family_breast else 24,
                    next_due=today + timedelta(days=30),
                    rationale=(
                        "Theo guideline, nữ 40–74 tuổi nên chụp nhũ ảnh định kỳ; "
                        "tiền sử gia đình → rút ngắn khoảng cách."
                    ),
                    sources=[_SRC_BREAST],
                    priority=1,
                )
            )
        if p.gender.value == "female" and 30 <= p.age <= 65:
            items.append(
                PlanItem(
                    cancer_type=CancerType.cervical,
                    method="Xét nghiệm HPV DNA",
                    start_age=30,
                    interval_months=60,
                    next_due=today + timedelta(days=60),
                    rationale="Xét nghiệm HPV mỗi 5–10 năm từ 30 tuổi.",
                    sources=[_SRC_CERV],
                    priority=2,
                )
            )
        smoking = bool(p.lifestyle.get("smoking")) or any(
            a.question_id == "smoking" and a.value in (True, "true", "yes") for a in ctx.answers
        )
        pack_years = float(p.lifestyle.get("pack_years") or 0)
        for a in ctx.answers:
            if a.question_id == "pack_years":
                try:
                    pack_years = float(a.value)
                except (TypeError, ValueError):
                    pass
        if smoking and p.age >= 50 and pack_years >= 20:
            factors.append(
                RiskFactor(
                    cancer_type=CancerType.lung, level=RiskLevel.high, reasons=[f"Hút thuốc {pack_years:g} gói-năm"]
                )
            )
            items.append(
                PlanItem(
                    cancer_type=CancerType.lung,
                    method="CT liều thấp (LDCT) phổi",
                    start_age=50,
                    interval_months=12,
                    next_due=today + timedelta(days=14),
                    rationale=("Người 50–80 tuổi, ≥20 gói-năm, đang hút hoặc bỏ <15 năm nên chụp LDCT hàng năm."),
                    sources=[_SRC_LUNG],
                    priority=1,
                )
            )
        if p.age >= 45:
            items.append(
                PlanItem(
                    cancer_type=CancerType.colorectal,
                    method="Nội soi đại tràng (hoặc FIT hàng năm)",
                    start_age=45,
                    interval_months=120,
                    next_due=today + timedelta(days=90),
                    rationale="Người 45–75 tuổi nên tầm soát ung thư đại trực tràng.",
                    sources=[_SRC_CRC],
                    priority=3,
                )
            )
        if not items:
            # luôn có ít nhất 1 item để FE có gì hiển thị (case trẻ, nguy cơ trung bình)
            items.append(
                PlanItem(
                    cancer_type=CancerType.other,
                    method="Khám sức khoẻ tổng quát định kỳ",
                    interval_months=12,
                    next_due=today + timedelta(days=180),
                    rationale="Chưa đến tuổi/nhóm nguy cơ cần tầm soát chuyên biệt theo guideline hiện có.",
                    sources=[_SRC_CRC],
                    priority=5,
                )
            )

        plan = ScreeningPlan(
            items=items,
            general_advice="Duy trì lối sống lành mạnh; trao đổi với bác sĩ về kế hoạch phù hợp với bạn.",
            generated_at=datetime.now(),
            model="mock",
        )
        risk = RiskAssessment(
            overall_summary="(MOCK) Đánh giá sơ bộ dựa trên tuổi, giới, tiền sử gia đình và lối sống.",
            factors=factors,
        )
        return ScreeningResult(
            status="pending_review",
            risk_assessment=risk,
            draft_plan=plan,
            disclaimer=DISCLAIMER_VI,
            trace_id=trace_id,
        )

    def get_education(self, cancer_type: CancerType) -> EducationContent:
        return EducationContent(
            cancer_type=cancer_type,
            title=f"(MOCK) Hiểu về tầm soát ung thư {cancer_type.value}",
            warning_signs=["Khối u bất thường", "Chảy máu bất thường", "Sụt cân không rõ nguyên nhân"],
            prevention_tips=["Không hút thuốc", "Vận động đều đặn", "Tầm soát đúng lịch"],
            body_md="Nội dung giáo dục sẽ được lấy từ guideline (TODO).",
            sources=[_SRC_CRC],
        )
