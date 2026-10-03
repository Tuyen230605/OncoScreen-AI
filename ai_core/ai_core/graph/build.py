"""Lắp ráp LangGraph: collect → red_flag → (END | assess_risk → retrieve → recommend → guardrail) → END."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from ai_core.graph.nodes import assess_risk, collect, guardrail, recommend, red_flag, retrieve
from ai_core.graph.state import AgentState


def _after_red_flag(state: AgentState) -> str:
    rf = state.get("red_flag")
    if rf and rf.detected:
        return END
    missing = state.get("missing_questions", [])
    if missing:
        raise ValueError("missing required questions: " + ", ".join(missing))
    return "assess_risk"


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("collect", collect.run)
    g.add_node("red_flag", red_flag.run)
    g.add_node("assess_risk", assess_risk.run)
    g.add_node("retrieve", retrieve.run)
    g.add_node("recommend", recommend.run)
    g.add_node("guardrail", guardrail.run)

    g.set_entry_point("collect")
    g.add_edge("collect", "red_flag")
    g.add_conditional_edges("red_flag", _after_red_flag, {END: END, "assess_risk": "assess_risk"})
    g.add_edge("assess_risk", "retrieve")
    g.add_edge("retrieve", "recommend")
    g.add_edge("recommend", "guardrail")
    g.add_edge("guardrail", END)
    return g.compile()
