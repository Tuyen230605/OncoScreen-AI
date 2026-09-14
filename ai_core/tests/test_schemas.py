from datetime import date, datetime

import pytest
from pydantic import ValidationError

from ai_core.schemas import CancerType, PlanItem, ScreeningPlan, ScreeningResult, Source


def _item() -> PlanItem:
    return PlanItem(
        cancer_type=CancerType.breast,
        method="Nhũ ảnh",
        interval_months=24,
        next_due=date.today(),
        rationale="theo guideline",
        sources=[Source(doc_id="d", title="t", excerpt="e")],
    )


def test_plan_item_requires_source():
    with pytest.raises(ValidationError):
        PlanItem(
            cancer_type=CancerType.breast,
            method="x",
            interval_months=12,
            next_due=date.today(),
            rationale="r",
            sources=[],
        )


def test_red_flag_result_cannot_have_plan():
    plan = ScreeningPlan(items=[_item()], generated_at=datetime.now(), model="mock")
    with pytest.raises(ValidationError):
        ScreeningResult(status="red_flag", draft_plan=plan, disclaimer="d", trace_id="t")


def test_plan_roundtrip_json():
    plan = ScreeningPlan(items=[_item()], generated_at=datetime.now(), model="mock")
    dumped = plan.model_dump(mode="json")
    assert ScreeningPlan.model_validate(dumped) == plan
