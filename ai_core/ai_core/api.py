"""★ Entry point duy nhất backend được import.

from ai_core.api import get_agent, AgentError
agent = get_agent()          # Agent thật (LLM) hoặc MockAgent (xác định, không cần key) tuỳ USE_MOCK_AGENT

Hai agent dùng chung lõi (luật tầm soát, RAG, guardrails, tracing):
- Navigator: người dùng ẩn danh hỏi về tầm soát → gợi ý theo nhóm + điều hướng đặt lịch.
- Clinical Copilot: bác sĩ đọc hồ sơ xuyên suốt → tóm tắt trước khám + bản nháp kế hoạch để duyệt.
"""

from __future__ import annotations

from typing import Protocol

from ai_core.config import settings
from ai_core.errors import AgentError
from ai_core.schemas import (
    Answer,
    CancerType,
    ChatTurn,
    ClinicalBrief,
    EducationContent,
    IntakeProfile,
    NavigatorReply,
    PatientProfile,
    PatientRecord,
    QuestionAnswer,
    Questionnaire,
    RedFlagResult,
    ScreeningPlan,
)

__all__ = [
    "CANCER_LABEL_VI",
    "Agent",
    "AgentError",
    "AgentProtocol",
    "get_agent",
    "intake_from_profile",
    "list_services",
    "merge_intake",
    "genetics_codes_from_intake",
]


class AgentProtocol(Protocol):
    name: str

    # Navigator — người dùng (không cần đăng nhập)
    def navigator_questionnaire(self) -> Questionnaire: ...
    def navigate(
        self, *, message: str | None, answers: list[Answer], intake: IntakeProfile, history: list[ChatTurn]
    ) -> NavigatorReply: ...
    def check_red_flags(self, answers: list[Answer], text: str | None = None) -> RedFlagResult: ...

    # Clinical Copilot — bác sĩ
    def build_brief(self, record: PatientRecord) -> ClinicalBrief: ...
    def ask_copilot(self, question: str, record: PatientRecord, history: list[ChatTurn]) -> QuestionAnswer: ...

    # Sau khi bác sĩ duyệt — bệnh nhân
    def answer_question(self, question: str, approved_plan: ScreeningPlan | None) -> QuestionAnswer: ...
    def get_education(self, cancer_type: CancerType) -> EducationContent: ...


class Agent:
    """Agent thật: LangGraph + RAG lai + LLM; mọi bước LLM có fallback xác định và guardrail đầu ra."""

    name = "real"

    def __init__(self, use_llm: bool = True, dense: bool = True) -> None:
        from ai_core.agents.copilot import ClinicalCopilot
        from ai_core.agents.navigator import NavigatorAgent

        self._use_llm = use_llm
        self._navigator = NavigatorAgent(use_llm=use_llm, dense=dense)
        self._copilot = ClinicalCopilot(use_llm=use_llm, dense=dense)

    def navigator_questionnaire(self) -> Questionnaire:
        from ai_core.tools.questionnaire import load_questionnaire

        try:
            return load_questionnaire()
        except Exception as exc:  # noqa: BLE001 — contract §1: lỗi nội bộ → AgentError
            raise AgentError(str(exc)) from exc

    def navigate(
        self, *, message: str | None, answers: list[Answer], intake: IntakeProfile, history: list[ChatTurn]
    ) -> NavigatorReply:
        try:
            return self._navigator.run(message=message, answers=answers, intake=intake, history=history)
        except Exception as exc:  # noqa: BLE001 — bọc mọi lỗi nội bộ thành AgentError
            raise AgentError(str(exc)) from exc

    def check_red_flags(self, answers: list[Answer], text: str | None = None) -> RedFlagResult:
        from ai_core.tools.red_flag_detector import detect_red_flags

        try:
            return detect_red_flags(answers, text)
        except Exception as exc:  # noqa: BLE001
            raise AgentError(str(exc)) from exc

    def build_brief(self, record: PatientRecord) -> ClinicalBrief:
        try:
            return self._copilot.build_brief(record)
        except Exception as exc:  # noqa: BLE001
            raise AgentError(str(exc)) from exc

    def ask_copilot(self, question: str, record: PatientRecord, history: list[ChatTurn]) -> QuestionAnswer:
        try:
            return self._copilot.ask(question, record, history)
        except Exception as exc:  # noqa: BLE001
            raise AgentError(str(exc)) from exc

    def answer_question(self, question: str, approved_plan: ScreeningPlan | None) -> QuestionAnswer:
        from ai_core.tools.patient_qa import answer_question

        try:
            return answer_question(question, approved_plan, use_llm=self._use_llm)
        except Exception as exc:  # noqa: BLE001
            raise AgentError(str(exc)) from exc

    def get_education(self, cancer_type: CancerType) -> EducationContent:
        from ai_core.tools.education import get_education_content

        try:
            return get_education_content(cancer_type)
        except Exception as exc:  # noqa: BLE001
            raise AgentError(str(exc)) from exc


# --------------------------------------------------------------------------- helpers cho backend

from ai_core.tools.eligibility import LABEL_VI as CANCER_LABEL_VI  # noqa: E402 — nhãn tiếng Việt cho UI/hồ sơ


def list_services() -> list[dict]:
    """Danh mục dịch vụ đặt lịch (mô phỏng) mà Navigator có thể gợi ý."""
    from ai_core.tools.triage import load_services

    return load_services()


def intake_from_profile(profile: PatientProfile) -> IntakeProfile:
    from ai_core.tools.intake import from_profile

    return from_profile(profile)


def merge_intake(primary: IntakeProfile | None, secondary: IntakeProfile | None) -> IntakeProfile:
    from ai_core.tools.intake import merge

    return merge(primary, secondary)


def genetics_codes_from_intake(intake: IntakeProfile) -> list[str]:
    from ai_core.tools.intake import to_genetics_codes

    return to_genetics_codes(intake)


_agent: AgentProtocol | None = None


def get_agent(force_mock: bool | None = None) -> AgentProtocol:
    """Singleton. `force_mock` dùng trong test; mặc định theo settings.use_mock_agent."""
    global _agent
    use_mock = settings.use_mock_agent if force_mock is None else force_mock
    if _agent is None or _agent.name != ("mock" if use_mock else "real"):
        if use_mock:
            from ai_core.mock import MockAgent

            _agent = MockAgent()
        else:
            _agent = Agent()
    return _agent
