"""★ Entry point duy nhất backend được import.

from ai_core.api import get_agent, AgentError
agent = get_agent()          # ScreeningAgent (thật) hoặc MockAgent tuỳ USE_MOCK_AGENT
"""

from __future__ import annotations

from typing import Protocol

from ai_core.config import settings
from ai_core.errors import AgentError
from ai_core.schemas import (
    Answer,
    CancerType,
    EducationContent,
    PatientContext,
    PatientProfile,
    Questionnaire,
    RedFlagResult,
    ScreeningResult,
)


class ScreeningAgentProtocol(Protocol):
    name: str

    def get_questionnaire(self, profile: PatientProfile) -> Questionnaire: ...
    def check_red_flags(self, answers: list[Answer]) -> RedFlagResult: ...
    def missing_questions(self, profile: PatientProfile, answers: list[Answer]) -> list[str]:
        """Trả danh sách question_id còn thiếu (rỗng = đủ để chạy screening)."""
        ...

    def run_screening(self, ctx: PatientContext) -> ScreeningResult: ...
    def get_education(self, cancer_type: CancerType) -> EducationContent: ...


class ScreeningAgent:
    """Agent thật: LangGraph + RAG. TODO(Tuyền): hoàn thiện theo GUIDE_AI_CORE.md mục 1.3."""

    name = "real"

    def __init__(self) -> None:
        from ai_core.graph.build import build_graph

        self._graph = build_graph()

    def get_questionnaire(self, profile: PatientProfile) -> Questionnaire:
        from ai_core.tools.questionnaire import build_questionnaire

        return build_questionnaire(profile)

    def check_red_flags(self, answers: list[Answer]) -> RedFlagResult:
        from ai_core.tools.red_flag_detector import detect_red_flags

        return detect_red_flags(answers)

    def missing_questions(self, profile: PatientProfile, answers: list[Answer]) -> list[str]:
        from ai_core.tools.questionnaire import missing_required

        return missing_required(profile, answers)

    def run_screening(self, ctx: PatientContext) -> ScreeningResult:
        from ai_core.graph.state import initial_state, state_to_result

        try:
            final_state = self._graph.invoke(initial_state(ctx))
        except Exception as exc:  # noqa: BLE001 — bọc mọi lỗi nội bộ thành AgentError
            raise AgentError(str(exc)) from exc
        return state_to_result(final_state)

    def get_education(self, cancer_type: CancerType) -> EducationContent:
        from ai_core.tools.education import get_education_content

        return get_education_content(cancer_type)


_agent: ScreeningAgentProtocol | None = None


def get_agent(force_mock: bool | None = None) -> ScreeningAgentProtocol:
    """Singleton. `force_mock` dùng trong test; mặc định theo settings.use_mock_agent."""
    global _agent
    use_mock = settings.use_mock_agent if force_mock is None else force_mock
    if _agent is None or _agent.name != ("mock" if use_mock else "real"):
        if use_mock:
            from ai_core.mock import MockAgent

            _agent = MockAgent()
        else:
            _agent = ScreeningAgent()
    return _agent
