from datetime import date, datetime

import pytest

from ai_core.guardrails.safety import GuardrailViolation, find_diagnosis_language, validate_plan
from ai_core.schemas import CancerType, PlanItem, ScreeningPlan, Source


def _plan(rationale: str) -> ScreeningPlan:
    item = PlanItem(
        cancer_type=CancerType.lung,
        method="LDCT",
        interval_months=12,
        next_due=date.today(),
        rationale=rationale,
        sources=[Source(doc_id="d", title="t", excerpt="e")],
    )
    return ScreeningPlan(items=[item], generated_at=datetime.now(), model="test")


def test_blocks_diagnosis_language():
    with pytest.raises(GuardrailViolation):
        validate_plan(_plan("Bạn bị ung thư phổi giai đoạn sớm."))


def test_allows_neutral_language():
    validate_plan(_plan("Theo guideline, người hút thuốc ≥20 gói-năm nên chụp LDCT hàng năm."))


def test_find_diagnosis_language():
    assert find_diagnosis_language("bạn đang mắc bệnh")
    assert not find_diagnosis_language("nên tầm soát định kỳ")
