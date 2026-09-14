"""Tool: screening recommender — gọi LLM với structured output, CHỈ dựa trên sources.

TODO(Tuyền): implement. Gợi ý:
    llm = get_chat_model().with_structured_output(ScreeningPlanDraft)   # pydantic
    prompt = RECOMMEND_PROMPT.format(profile=..., risk_assessment=..., sources=...)
    → map doc_id trong output về Source thật (không tin LLM tự chép excerpt)
"""

from __future__ import annotations

from ai_core.schemas import PatientProfile, RiskAssessment, ScreeningPlan, Source


def recommend(profile: PatientProfile, risk: RiskAssessment, sources: list[Source]) -> ScreeningPlan:
    raise NotImplementedError("TODO(Tuyền): screening_recommender.recommend")
