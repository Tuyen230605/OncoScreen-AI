from datetime import date, datetime

import pytest
from pydantic import ValidationError

from ai_core.schemas import (
    BookingHint,
    BookingPriority,
    CancerType,
    IntakeProfile,
    NavigatorReply,
    NextAction,
    PlanItem,
    RedFlag,
    RedFlagResult,
    RedFlagSeverity,
    ScreeningPlan,
    ScreeningSuggestion,
    Source,
)

SRC = Source(doc_id="d", title="t", excerpt="e")
FLAG = RedFlag(code="symptom_lump", symptom="Khối u", severity=RedFlagSeverity.urgent, advice="Đi khám")


def _item() -> PlanItem:
    return PlanItem(
        cancer_type=CancerType.breast,
        method="Nhũ ảnh",
        interval_months=24,
        next_due=date.today(),
        rationale="theo guideline",
        sources=[SRC],
    )


def _reply(**kw) -> NavigatorReply:
    base = dict(
        reply="ok",
        intake=IntakeProfile(),
        red_flag=RedFlagResult(detected=False),
        next_action=NextAction.continue_chat,
        disclaimer="d",
        trace_id="t",
    )
    return NavigatorReply(**{**base, **kw})


def test_plan_item_and_suggestion_require_source():
    with pytest.raises(ValidationError):
        PlanItem(cancer_type=CancerType.breast, method="x", interval_months=12, rationale="r", sources=[])
    with pytest.raises(ValidationError):
        ScreeningSuggestion(rule_id="r", cancer_type=CancerType.breast, method="m", applies_because="a", sources=[])


def test_plan_roundtrip_json():
    plan = ScreeningPlan(items=[_item()], generated_at=datetime.now(), model="mock")
    assert ScreeningPlan.model_validate(plan.model_dump(mode="json")) == plan


def test_red_flag_reply_must_route_to_urgent_care_without_suggestions():
    rf = RedFlagResult(detected=True, flags=[FLAG], message="m")
    hint = BookingHint(priority=BookingPriority.urgent, service_codes=["oncology_priority"], reason="r")
    assert (
        _reply(red_flag=rf, next_action=NextAction.urgent_care, booking_hint=hint).next_action == NextAction.urgent_care
    )
    with pytest.raises(ValidationError):
        _reply(red_flag=rf, next_action=NextAction.suggest_booking, booking_hint=hint)
    suggestion = ScreeningSuggestion(
        rule_id="r", cancer_type=CancerType.breast, method="m", applies_because="a", sources=[SRC]
    )
    with pytest.raises(ValidationError):
        _reply(red_flag=rf, next_action=NextAction.urgent_care, booking_hint=hint, suggestions=[suggestion])


def test_urgent_care_requires_red_flag_and_booking_requires_hint():
    with pytest.raises(ValidationError):
        _reply(next_action=NextAction.urgent_care)
    with pytest.raises(ValidationError):
        _reply(next_action=NextAction.suggest_booking)


def test_detected_red_flag_requires_message_and_flags():
    with pytest.raises(ValidationError):
        RedFlagResult(detected=True)


def test_red_flag_reply_requires_urgent_booking_priority():
    """Contract §3.1: red_flag.detected ⇒ booking_hint.priority = urgent."""
    rf = RedFlagResult(detected=True, flags=[FLAG], message="m")
    routine = BookingHint(priority=BookingPriority.routine, service_codes=["general_screening"], reason="r")
    with pytest.raises(ValidationError):
        _reply(red_flag=rf, next_action=NextAction.urgent_care, booking_hint=routine)
