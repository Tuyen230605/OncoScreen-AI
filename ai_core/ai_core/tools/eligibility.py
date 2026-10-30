"""Tool: eligibility engine — luật xác định (data/screening_rules.json) → mốc tầm soát theo nhóm, có nguồn.

"Rules-first, LLM-second": việc QUYẾT ĐỊNH loại tầm soát, tuổi bắt đầu, chu kỳ không giao cho LLM.
Mỗi luật trỏ tới một mục guideline cụ thể; luật trỏ sai doc/section làm hỏng ngay lúc load (fail fast).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache

from ai_core.config import DATA_DIR
from ai_core.rag.corpus import source_for
from ai_core.schemas import CancerType, IntakeProfile, RiskFactor, RiskLevel, ScreeningSuggestion, Source

LABEL_VI = {
    CancerType.breast: "ung thư vú",
    CancerType.cervical: "ung thư cổ tử cung",
    CancerType.colorectal: "ung thư đại trực tràng",
    CancerType.liver: "ung thư gan",
    CancerType.lung: "ung thư phổi",
    CancerType.prostate: "ung thư tuyến tiền liệt",
    CancerType.other: "ung thư khác",
}


@dataclass(frozen=True)
class Rule:
    id: str
    cancer_type: CancerType
    doc_id: str
    section: str
    gender: str
    min_age: int
    max_age: int | None
    requires: tuple[str, ...]
    method: str
    start_age: int | None
    interval_months: int | None
    applies_because: str
    family_note: str | None
    source: Source


@dataclass
class EligibilityResult:
    suggestions: list[ScreeningSuggestion] = field(default_factory=list)
    risk_factors: list[RiskFactor] = field(default_factory=list)
    evaluated: bool = False  # False khi chưa đủ tuổi/giới để áp luật


@lru_cache(maxsize=1)
def load_rules() -> tuple[Rule, ...]:
    raw = json.loads((DATA_DIR / "screening_rules.json").read_text(encoding="utf-8"))
    rules = []
    for r in raw["rules"]:
        rules.append(
            Rule(
                id=r["id"],
                cancer_type=CancerType(r["cancer_type"]),
                doc_id=r["doc_id"],
                section=r["section"],
                gender=r["gender"],
                min_age=int(r["min_age"]),
                max_age=r.get("max_age"),
                requires=tuple(r.get("requires", [])),
                method=r["method"],
                start_age=r.get("start_age"),
                interval_months=r.get("interval_months"),
                applies_because=r["applies_because"],
                family_note=r.get("family_note"),
                source=source_for(r["doc_id"], r["section"]),
            )
        )
    return tuple(rules)


def _requirement_met(req: str, intake: IntakeProfile) -> bool | None:
    """True/False khi xác định được; None khi còn thiếu dữ liệu để kết luận."""
    if req == "pack_years>=20":
        if intake.smoking is False:
            return False
        if intake.pack_years is None:
            return None if intake.smoking else False
        return intake.pack_years >= 20
    if req == "cirrhosis":
        return bool(intake.cirrhosis)
    if req == "hepatitis_without_cirrhosis":
        # AASLD 2023 ("Đối tượng"): chỉ một số người viêm gan B mạn cần giám sát; viêm gan C mạn cần đánh giá xơ hoá
        # trước → không tự đặt chu kỳ, chỉ gợi ý trao đổi với bác sĩ.
        return bool(intake.hepatitis_b_or_c) and not intake.cirrhosis
    if req == "hepatitis_or_cirrhosis":
        return bool(intake.hepatitis_b_or_c or intake.cirrhosis)
    raise ValueError(f"unknown requirement {req!r}")


def evaluate(intake: IntakeProfile) -> EligibilityResult:
    if intake.age is None or intake.gender is None:
        return EligibilityResult()
    result = EligibilityResult(evaluated=True)
    risk: dict[CancerType, RiskFactor] = {}

    def add_risk(cancer_type: CancerType, level: RiskLevel, reason: str) -> None:
        current = risk.get(cancer_type)
        order = [RiskLevel.average, RiskLevel.elevated, RiskLevel.high]
        if current is None:
            risk[cancer_type] = RiskFactor(cancer_type=cancer_type, level=level, reasons=[reason])
            return
        current.reasons.append(reason)
        if order.index(level) > order.index(current.level):
            current.level = level

    for cancer_type in intake.family_history:
        if cancer_type != CancerType.other:
            add_risk(cancer_type, RiskLevel.elevated, f"Có người thân mắc {LABEL_VI[cancer_type]}")
    if intake.smoking and (intake.pack_years or 0) >= 20:
        add_risk(CancerType.lung, RiskLevel.high, f"Hút thuốc {intake.pack_years:g} gói-năm")
    if intake.hepatitis_b_or_c:
        add_risk(CancerType.liver, RiskLevel.high, "Viêm gan B/C mạn tính")
    if intake.cirrhosis:
        add_risk(CancerType.liver, RiskLevel.high, "Xơ gan")

    if intake.personal_cancer_history:
        # Guideline tầm soát dành cho người chưa mắc bệnh; người đã từng mắc ung thư cần kế hoạch theo dõi chuyên khoa.
        result.risk_factors = list(risk.values())
        return result

    for rule in load_rules():
        if rule.gender != "any" and rule.gender != intake.gender.value:
            continue
        if intake.age < rule.min_age or (rule.max_age is not None and intake.age > rule.max_age):
            continue
        if not all(_requirement_met(req, intake) for req in rule.requires):
            continue
        family = rule.cancer_type in intake.family_history
        result.suggestions.append(
            ScreeningSuggestion(
                rule_id=rule.id,
                cancer_type=rule.cancer_type,
                method=rule.method,
                start_age=rule.start_age,
                interval_months=rule.interval_months,
                applies_because=rule.applies_because,
                note=rule.family_note if family else None,
                elevated_risk=family or rule.cancer_type in risk and risk[rule.cancer_type].level != RiskLevel.average,
                sources=[rule.source],
            )
        )
    result.risk_factors = list(risk.values())
    return result
