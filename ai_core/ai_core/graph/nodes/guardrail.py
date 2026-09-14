"""Node guardrail: validate plan (S1, S2). Vi phạm → raise (api.py bọc thành AgentError).

TODO(Tuyền): retry recommend 1 lần với feedback trước khi fail hẳn.
"""

from __future__ import annotations

from ai_core.graph.state import AgentState
from ai_core.guardrails.safety import validate_plan


def run(state: AgentState) -> AgentState:
    plan = state.get("draft_plan")
    if plan is None:
        raise RuntimeError("no draft_plan to validate")
    return {"draft_plan": validate_plan(plan)}
