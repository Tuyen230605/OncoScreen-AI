"""Node assess_risk: LLM (structured output) + rule → RiskAssessment.

TODO(Tuyền): llm = get_chat_model().with_structured_output(RiskAssessment)
"""

from __future__ import annotations

from ai_core.graph.state import AgentState


def run(state: AgentState) -> AgentState:
    raise NotImplementedError("TODO(Tuyền): nodes.assess_risk")
