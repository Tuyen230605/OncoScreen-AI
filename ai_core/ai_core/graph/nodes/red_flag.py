"""Node red_flag: rule-based detector. Nếu detected → graph kết thúc (không gọi LLM)."""

from __future__ import annotations

from ai_core.graph.state import AgentState
from ai_core.tools.red_flag_detector import detect_red_flags


def run(state: AgentState) -> AgentState:
    return {"red_flag": detect_red_flags(state["ctx"].answers)}
