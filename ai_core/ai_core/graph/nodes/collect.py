"""Node collect: xác định câu hỏi còn thiếu (rule-based)."""

from __future__ import annotations

from ai_core.graph.state import AgentState
from ai_core.tools.questionnaire import missing_required


def run(state: AgentState) -> AgentState:
    ctx = state["ctx"]
    return {"missing_questions": missing_required(ctx.profile, ctx.answers)}
