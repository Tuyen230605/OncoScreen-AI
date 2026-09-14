"""Node retrieve: RAG — lọc metadata (gender, tuổi) rồi similarity search → list[Source]."""

from __future__ import annotations

from ai_core.graph.state import AgentState
from ai_core.rag.retriever import retrieve_sources


def run(state: AgentState) -> AgentState:
    ctx = state["ctx"]
    risk = state.get("risk_assessment")
    return {"sources": retrieve_sources(ctx.profile, risk)}
