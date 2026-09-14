"""Node recommend: gọi tools.screening_recommender → ScreeningPlan (draft)."""

from __future__ import annotations

from ai_core.graph.state import AgentState
from ai_core.tools.screening_recommender import recommend


def run(state: AgentState) -> AgentState:
    ctx = state["ctx"]
    risk = state.get("risk_assessment")
    if risk is None:
        raise RuntimeError("assess_risk must run before recommend")
    return {"draft_plan": recommend(ctx.profile, risk, state.get("sources", []))}
