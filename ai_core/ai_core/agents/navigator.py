"""Navigator Agent — trợ lý tầm soát cho người dùng ẩn danh.

LangGraph:
    input_guard → update_intake ─┬─(red-flag)──────────────────────────────→ triage → END
                                 └→ eligibility ─┬─(có câu hỏi tự do)→ retrieve → respond → triage → END
                                                 └────────────────────────────→ respond → triage → END

- Red-flag (rule-based) ngắt luồng trước mọi bước LLM/RAG.
- Mốc tầm soát do eligibility engine (luật + nguồn) quyết định; LLM chỉ diễn giải.
- Câu trả lời LLM phải qua output guard (ngôn ngữ chẩn đoán, trích dẫn hợp lệ, con số có trong bằng chứng);
  vi phạm hoặc LLM lỗi → câu trả lời mẫu xác định (fail-safe).
"""

from __future__ import annotations

import json
import logging
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from ai_core.guardrails.disclaimer import DISCLAIMER_VI
from ai_core.guardrails.safety import (
    is_out_of_scope_request,
    looks_like_prompt_injection,
    ungrounded_numbers,
    unsafe_output,
)
from ai_core.observability import new_trace_id, traced
from ai_core.prompts import NAVIGATOR_PROMPT, NAVIGATOR_SYSTEM_PROMPT
from ai_core.rag.retriever import retrieve
from ai_core.schemas import (
    Answer,
    BookingHint,
    ChatTurn,
    Gender,
    IntakeProfile,
    NavigatorReply,
    NextAction,
    RedFlagResult,
    RiskFactor,
    RiskLevel,
    ScreeningSuggestion,
    Source,
)
from ai_core.tools import intake as intake_tool
from ai_core.tools.eligibility import LABEL_VI, evaluate
from ai_core.tools.red_flag_detector import flags_for_codes, relative_codes_from_text, result_for_codes
from ai_core.tools.triage import triage

logger = logging.getLogger(__name__)
AGENT = "navigator"

_GENDER_VI = {Gender.female: "nữ", Gender.male: "nam", Gender.other: "giới tính khác"}
_MISSING_VI = {"age": "tuổi", "gender": "giới tính", "pack_years": "số gói-năm đã hút (số gói/ngày × số năm)"}
ABSTAIN_VI = (
    "Mình chưa đủ thông tin từ các hướng dẫn hiện có để trả lời chính xác câu hỏi này; "
    "bạn nên trao đổi trực tiếp với bác sĩ."
)


class NavigatorState(TypedDict, total=False):
    message: str | None
    answers: list[Answer]
    history: list[ChatTurn]
    intake: IntakeProfile
    trace_id: str
    trace_events: list[dict]
    out_of_scope: bool
    injection: bool
    red_flag: RedFlagResult
    relative_flags: list[str]
    missing: list[str]
    suggestions: list[ScreeningSuggestion]
    risk_factors: list[RiskFactor]
    evaluated: bool
    sources: list[Source]
    reply: str
    reply_sources: list[Source]
    insufficient: bool
    next_action: NextAction
    booking_hint: BookingHint | None


class _ExtractedIntake(BaseModel):
    """Chỉ trích xuất điều người dùng NÓI RÕ; không suy đoán."""

    age: int | None = Field(default=None, ge=0, le=120)
    gender: Gender | None = None
    smoking: bool | None = None
    pack_years: float | None = Field(default=None, ge=0)
    hepatitis_b_or_c: bool | None = None


class _DraftReply(BaseModel):
    reply: str
    source_ids: list[str] = Field(default_factory=list)
    insufficient_evidence: bool = False


def interval_vi(months: int | None) -> str:
    if months is None:
        return "tần suất do bác sĩ cùng bạn quyết định"
    if months % 12 == 0:
        years = months // 12
        return "mỗi năm" if years == 1 else f"mỗi {years} năm"
    return f"mỗi {months} tháng"


def summarize_suggestions(suggestions: list[ScreeningSuggestion]) -> list[str]:
    lines = []
    for s in suggestions:
        label = LABEL_VI[s.cancer_type].capitalize()
        line = f"• {label}: {s.method}, {interval_vi(s.interval_months)} ({s.applies_because})."
        if s.note:
            line += f" Lưu ý: {s.note}"
        lines.append(line)
    return lines


class NavigatorAgent:
    def __init__(self, use_llm: bool = True, dense: bool = True) -> None:
        self.use_llm = use_llm
        self.dense = dense
        self._graph = self._build()

    # ------------------------------------------------------------------ graph

    def _build(self):
        g = StateGraph(NavigatorState)
        for name, fn in [
            ("input_guard", self._input_guard),
            ("update_intake", self._update_intake),
            ("eligibility", self._eligibility),
            ("retrieve", self._retrieve),
            ("respond", self._respond),
            ("triage", self._triage),
        ]:
            g.add_node(name, traced(AGENT, name, fn))
        g.set_entry_point("input_guard")
        g.add_edge("input_guard", "update_intake")
        g.add_conditional_edges(
            "update_intake",
            lambda s: "triage" if s["red_flag"].detected else "eligibility",
            {"triage": "triage", "eligibility": "eligibility"},
        )
        g.add_conditional_edges(
            "eligibility",
            lambda s: "retrieve" if s.get("message") and not s.get("out_of_scope") else "respond",
            {"retrieve": "retrieve", "respond": "respond"},
        )
        g.add_edge("retrieve", "respond")
        g.add_edge("respond", "triage")
        g.add_edge("triage", END)
        return g.compile()

    def run(
        self,
        *,
        message: str | None,
        answers: list[Answer],
        intake: IntakeProfile,
        history: list[ChatTurn],
    ) -> NavigatorReply:
        state = self._graph.invoke(
            NavigatorState(
                message=(message or "").strip() or None,
                answers=answers,
                # Lượt cũ có dấu hiệu injection không được đưa vào prompt (chống injection qua lịch sử).
                history=[t for t in history if not looks_like_prompt_injection(t.content)][-8:],
                intake=intake,
                trace_id=new_trace_id("nav"),
                trace_events=[],
                sources=[],
            )
        )
        return NavigatorReply(
            reply=state["reply"],
            sources=state.get("reply_sources", []),
            intake=state["intake"],
            missing_info=state.get("missing", []),
            suggestions=state.get("suggestions", []),
            risk_factors=state.get("risk_factors", []),
            red_flag=state["red_flag"],
            next_action=state["next_action"],
            booking_hint=state.get("booking_hint"),
            insufficient_evidence=state.get("insufficient", False),
            disclaimer=DISCLAIMER_VI,
            trace_id=state["trace_id"],
            trace_events=state.get("trace_events", []),
        )

    # ------------------------------------------------------------------ nodes

    def _input_guard(self, state: NavigatorState) -> dict:
        message = state.get("message") or ""
        out_of_scope = bool(message) and is_out_of_scope_request(message)
        injection = bool(message) and looks_like_prompt_injection(message)
        return {
            "out_of_scope": out_of_scope,
            "injection": injection,
            "trace_attrs": {
                "out_of_scope": out_of_scope,
                "injection_suspected": injection,
                "has_message": bool(message),
            },
        }

    def _update_intake(self, state: NavigatorState) -> dict:
        intake = intake_tool.from_answers(state["intake"], state.get("answers", []))
        extractor = "rules"
        message = state.get("message")
        if message:
            intake = intake_tool.from_text(intake, message)
        # Red-flag tính từ luật TRƯỚC mọi lời gọi LLM (S3): có cờ thì không gọi LLM trích xuất.
        red_flag = result_for_codes(intake.symptom_codes)
        if (
            message
            and self.use_llm
            and not red_flag.detected
            and not state.get("injection")
            and intake_tool.missing_info(intake)
        ):
            extracted = self._llm_extract(message, state["trace_id"])
            if extracted is not None:
                intake = intake_tool.merge(intake, extracted)
                extractor = "rules+llm"
        return {
            "intake": intake,
            "red_flag": red_flag,
            "relative_flags": relative_codes_from_text(message) if message else [],
            "missing": intake_tool.missing_info(intake),
            "trace_attrs": {"extractor": extractor, "red_flag": red_flag.detected},
        }

    def _eligibility(self, state: NavigatorState) -> dict:
        result = evaluate(state["intake"])
        return {
            "suggestions": result.suggestions,
            "risk_factors": result.risk_factors,
            "evaluated": result.evaluated,
            "trace_attrs": {"suggestion_count": len(result.suggestions), "evaluated": result.evaluated},
        }

    def _retrieve(self, state: NavigatorState) -> dict:
        topics = " ".join(LABEL_VI[s.cancer_type] for s in state.get("suggestions", []))
        result = retrieve(f"{state['message']} {topics}".strip(), dense=self.dense)
        return {
            "sources": result.sources,
            "trace_attrs": {"source_count": len(result.sources), "mode": result.mode, "dense": result.dense_status},
        }

    def _respond(self, state: NavigatorState) -> dict:
        template, template_sources, insufficient = self._template(state)
        note = self._relative_note(state)
        if not (self.use_llm and state.get("message")) or state.get("out_of_scope") or state.get("injection"):
            return {
                "reply": note + template,
                "reply_sources": template_sources,
                "insufficient": insufficient,
                "trace_attrs": {"generator": "template"},
            }
        draft, problem = self._llm_reply(state)
        if draft is None and problem == "insufficient_evidence":
            # LLM tự nhận thiếu căn cứ → câu trả lời mẫu xác định, không dùng văn bản LLM.
            return {
                "reply": note + ABSTAIN_VI + "\n" + template,
                "reply_sources": template_sources,
                "insufficient": True,
                "trace_attrs": {"generator": "template_abstain", "guard": problem},
            }
        if draft is None:
            return {
                "reply": note + template,
                "reply_sources": template_sources,
                "insufficient": insufficient,
                "trace_attrs": {"generator": "template_fallback", "guard": problem},
            }
        reply, sources = draft
        return {
            "reply": note + reply,
            "reply_sources": sources,
            "insufficient": False,
            "trace_attrs": {"generator": "llm", "guard": "pass", "cited": len(sources)},
        }

    def _triage(self, state: NavigatorState) -> dict:
        red_flag = state["red_flag"]
        action, hint = triage(state["intake"], red_flag, state.get("suggestions", []), state.get("risk_factors", []))
        out: dict = {"next_action": action, "booking_hint": hint, "trace_attrs": {"next_action": action.value}}
        if red_flag.detected:
            lines = [red_flag.message or ""] + [f"• {f.symptom}: {f.advice}" for f in red_flag.flags]
            lines.append(
                "Bạn có thể tạo tài khoản để đặt lịch khám ưu tiên, hoặc đến cơ sở y tế gần nhất. "
                "Nếu triệu chứng nặng lên đột ngột, hãy gọi cấp cứu 115."
            )
            out.update(reply="\n".join(lines), reply_sources=[], suggestions=[], insufficient=False)
        return out

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _relative_note(state: NavigatorState) -> str:
        """Người dùng kể dấu hiệu cảnh báo của NGƯỜI THÂN: không ngắt luồng của người dùng,
        nhưng nhắc người thân đi khám sớm."""
        flags = flags_for_codes(state.get("relative_flags", []))
        if not flags:
            return ""
        symptoms = ", ".join(f.symptom.lower() for f in flags)
        return (
            f"Bạn có nhắc tới dấu hiệu ở người thân ({symptoms}): người thân nên được bác sĩ khám sớm, "
            "không chờ lịch tầm soát định kỳ.\n"
        )

    def _template(self, state: NavigatorState) -> tuple[str, list[Source], bool]:
        intake: IntakeProfile = state["intake"]
        suggestions = state.get("suggestions", [])
        risk_factors = state.get("risk_factors", [])
        missing = state.get("missing", [])
        message = state.get("message")
        parts: list[str] = []
        sources: list[Source] = [src for s in suggestions for src in s.sources]

        if state.get("out_of_scope"):
            parts.append(
                "Mình không thể chẩn đoán, đọc kết quả xét nghiệm/hình ảnh hay tư vấn điều trị — việc này cần bác sĩ "
                "đánh giá trực tiếp. Bạn có thể đặt lịch để được bác sĩ tư vấn."
            )
        if suggestions:
            who = f"{_GENDER_VI.get(intake.gender, '')}, {intake.age} tuổi".strip(", ")
            parts.append(f"Với thông tin bạn cung cấp ({who}), các hướng dẫn tầm soát hiện có gợi ý:")
            parts.extend(summarize_suggestions(suggestions))
        elif state.get("evaluated") and not intake.personal_cancer_history:
            parts.append(
                "Với độ tuổi và giới tính hiện tại, bộ hướng dẫn của hệ thống chưa có mốc tầm soát định kỳ nào "
                "áp dụng cho bạn."
            )
        if intake.personal_cancer_history:
            parts.append(
                "Bạn cho biết đã từng được chẩn đoán ung thư: các mốc tầm soát cho người chưa mắc bệnh không áp dụng; "
                "kế hoạch theo dõi cần bác sĩ chuyên khoa ung bướu xây dựng."
            )
        covered = {s.cancer_type for s in suggestions}
        for factor in risk_factors:
            if factor.level != RiskLevel.average and factor.cancer_type not in covered:
                parts.append(
                    f"Bạn có yếu tố cần lưu ý ({'; '.join(factor.reasons).lower()}) — nên trao đổi với bác sĩ về "
                    f"thời điểm và phương pháp tầm soát {LABEL_VI[factor.cancer_type]} phù hợp."
                )
        retrieved = [s for s in state.get("sources", []) if s.doc_id not in {x.doc_id for x in sources}]
        if message and not state.get("out_of_scope") and retrieved:
            top = retrieved[0]
            excerpt = top.excerpt.split("\n")[0][:300]
            parts.append(f"Thông tin liên quan từ {top.title} ({top.section}): {excerpt}")
            sources.append(top)
        if missing:
            parts.append(
                f"Để gợi ý chính xác hơn, bạn cho mình biết thêm {', '.join(_MISSING_VI[m] for m in missing)} nhé?"
            )
        if not parts:
            parts.append(
                "Mình là trợ lý tầm soát ung thư. Bạn có thể hỏi về loại ung thư nên tầm soát, thời điểm bắt đầu "
                "và tần suất; hoặc làm bảng hỏi nhanh để nhận gợi ý theo tuổi, giới và yếu tố nguy cơ."
            )
        insufficient = bool(message) and not state.get("out_of_scope") and not sources
        return "\n".join(parts), sources, insufficient

    def _llm_extract(self, message: str, trace_id: str) -> IntakeProfile | None:
        from ai_core.llm import get_chat_model

        try:
            model = get_chat_model().with_structured_output(_ExtractedIntake)
            raw = model.invoke(
                [
                    SystemMessage(
                        content="Trích xuất thông tin người dùng nói RÕ về bản thân. Không suy đoán; thiếu thì để null."
                    ),
                    HumanMessage(content=message),
                ]
            )
            data = _ExtractedIntake.model_validate(raw)
        except Exception as exc:  # noqa: BLE001 — trích xuất LLM chỉ là bổ trợ cho luật
            logger.warning("intake_llm_unavailable trace_id=%s error_type=%s", trace_id, type(exc).__name__)
            return None
        return IntakeProfile(**data.model_dump())

    def _llm_reply(self, state: NavigatorState) -> tuple[tuple[str, list[Source]] | None, str]:
        from ai_core.llm import get_chat_model

        suggestions = state.get("suggestions", [])
        allowed = {src.doc_id: src for s in suggestions for src in s.sources}
        for src in state.get("sources", []):
            allowed.setdefault(src.doc_id, src)
        intake_json = json.dumps(state["intake"].model_dump(mode="json"), ensure_ascii=False)
        suggestions_json = json.dumps(
            [s.model_dump(mode="json", exclude={"sources"}) for s in suggestions], ensure_ascii=False
        )
        prompt = NAVIGATOR_PROMPT.format(
            intake=intake_json,
            missing=", ".join(state.get("missing", [])) or "không",
            suggestions=suggestions_json,
            risk_factors=json.dumps(
                [f.model_dump(mode="json") for f in state.get("risk_factors", [])], ensure_ascii=False
            ),
            sources=json.dumps([s.model_dump(mode="json") for s in allowed.values()], ensure_ascii=False),
            history=json.dumps([t.model_dump() for t in state.get("history", [])], ensure_ascii=False),
            message=state["message"],
        )
        try:
            model = get_chat_model().with_structured_output(_DraftReply)
            draft = _DraftReply.model_validate(
                model.invoke([SystemMessage(content=NAVIGATOR_SYSTEM_PROMPT), HumanMessage(content=prompt)])
            )
        except Exception as exc:  # noqa: BLE001 — LLM lỗi → câu trả lời mẫu
            logger.warning("navigator_llm_unavailable trace_id=%s error_type=%s", state["trace_id"], type(exc).__name__)
            return None, "llm_error"
        reply = draft.reply.strip()
        citations = [allowed[d] for d in dict.fromkeys(draft.source_ids) if d in allowed]
        if not reply:
            return None, "empty"
        if problem := unsafe_output(reply):  # chẩn đoán / tư vấn điều trị / diễn giải kết quả
            return None, problem
        if draft.insufficient_evidence:
            return None, "insufficient_evidence"
        if not citations:
            return None, "uncited"
        evidence = [s.excerpt for s in allowed.values()] + [suggestions_json, intake_json, state["message"] or ""]
        if ungrounded_numbers(reply, evidence):
            return None, "ungrounded_number"
        return (reply, citations), "pass"
