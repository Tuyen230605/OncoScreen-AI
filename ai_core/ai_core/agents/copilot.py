"""Clinical Copilot — trợ lý cho bác sĩ, đọc hồ sơ xuyên suốt của bệnh nhân.

LangGraph (build_brief):
    load_record → eligibility → retrieve → draft_brief → draft_plan → END

- Dữ kiện (key_facts) luôn trỏ về RecordEvent.id; fact không truy vết được bị loại (chống bịa).
- Gợi ý theo guideline do eligibility engine sinh, có nguồn; có red-flag thì KHÔNG soạn kế hoạch tầm soát định kỳ.
- Bản nháp kế hoạch không có ngày hẹn; bác sĩ xác nhận ngày, sửa và phê duyệt (HITL) trước khi bệnh nhân thấy.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from ai_core.config import settings
from ai_core.guardrails.disclaimer import COPILOT_DISCLAIMER_VI
from ai_core.guardrails.safety import (
    is_out_of_scope_request,
    ungrounded_numbers,
    unsafe_output,
    validate_plan,
)
from ai_core.observability import new_trace_id, traced
from ai_core.prompts import COPILOT_BRIEF_PROMPT, COPILOT_QA_PROMPT, COPILOT_SYSTEM_PROMPT
from ai_core.rag.lexical import BM25, tokenize
from ai_core.rag.retriever import retrieve
from ai_core.schemas import (
    BriefFact,
    CancerType,
    ChatTurn,
    ClinicalBrief,
    Gender,
    IntakeProfile,
    PatientRecord,
    PlanItem,
    QuestionAnswer,
    RedFlag,
    RiskFactor,
    ScreeningPlan,
    ScreeningSuggestion,
    Source,
)
from ai_core.tools import intake as intake_tool
from ai_core.tools.eligibility import LABEL_VI, evaluate
from ai_core.tools.red_flag_detector import codes_from_text, result_for_codes

logger = logging.getLogger(__name__)
AGENT = "copilot"
FACT_KINDS = {"consult.summary", "red_flag.detected", "appointment.requested", "encounter.finalized", "reminder.done"}
# Kết luận bác sĩ đã viết (encounter.finalized) là đánh giá lâm sàng, không quét lại thành red-flag mới.
_NO_RED_FLAG_SCAN = {"encounter.finalized"}
_GENDER_VI = {Gender.female: "nữ", Gender.male: "nam", Gender.other: "giới tính khác"}


class CopilotState(TypedDict, total=False):
    record: PatientRecord
    intake: IntakeProfile
    trace_id: str
    trace_events: list[dict]
    facts: list[BriefFact]
    red_flags: list[RedFlag]
    suggestions: list[ScreeningSuggestion]
    risk_factors: list[RiskFactor]
    gaps: list[str]
    questions: list[str]
    sources: list[Source]
    summary: str
    draft_plan: ScreeningPlan | None


class _BriefDraft(BaseModel):
    summary: str
    key_facts: list[BriefFact] = Field(default_factory=list)
    questions_to_clarify: list[str] = Field(default_factory=list, max_length=5)


class _AnswerDraft(BaseModel):
    answer: str
    source_ids: list[str] = Field(default_factory=list)
    insufficient_evidence: bool = False


def record_sources(record: PatientRecord) -> list[Source]:
    return [
        Source(doc_id=f"record:{e.id}", title="Hồ sơ bệnh nhân", section=e.kind, excerpt=e.summary)
        for e in record.events
        if e.summary.strip()
    ]


class ClinicalCopilot:
    def __init__(self, use_llm: bool = True, dense: bool = True) -> None:
        self.use_llm = use_llm
        self.dense = dense
        self.model_name = settings.llm_model if use_llm else "mock"
        g = StateGraph(CopilotState)
        for name, fn in [
            ("load_record", self._load_record),
            ("eligibility", self._eligibility),
            ("retrieve", self._retrieve),
            ("draft_brief", self._draft_brief),
            ("draft_plan", self._draft_plan),
        ]:
            g.add_node(name, traced(AGENT, name, fn))
        g.set_entry_point("load_record")
        g.add_edge("load_record", "eligibility")
        g.add_edge("eligibility", "retrieve")
        g.add_edge("retrieve", "draft_brief")
        g.add_edge("draft_brief", "draft_plan")
        g.add_edge("draft_plan", END)
        self._graph = g.compile()

    # ------------------------------------------------------------------ brief

    def build_brief(self, record: PatientRecord) -> ClinicalBrief:
        state = self._graph.invoke(
            CopilotState(record=record, trace_id=new_trace_id("brief"), trace_events=[], sources=[])
        )
        return ClinicalBrief(
            summary=state["summary"],
            key_facts=state.get("facts", []),
            red_flags=state.get("red_flags", []),
            risk_factors=state.get("risk_factors", []),
            guideline_suggestions=state.get("suggestions", []),
            questions_to_clarify=state.get("questions", []),
            data_gaps=state.get("gaps", []),
            draft_plan=state.get("draft_plan"),
            disclaimer=COPILOT_DISCLAIMER_VI,
            generated_at=datetime.now(UTC),
            model=self.model_name,
            trace_id=state["trace_id"],
            trace_events=state.get("trace_events", []),
        )

    def _load_record(self, state: CopilotState) -> dict:
        record = state["record"]
        from_profile = intake_tool.from_profile(record.profile) if record.profile else None
        intake = intake_tool.merge(from_profile, record.intake)
        codes = list(intake.symptom_codes)
        # R2: triệu chứng nêu trong lý do khám hoặc tóm tắt hồ sơ (văn bản tự do) cũng là red-flag.
        codes += codes_from_text(record.reason_for_visit or "")
        for event in record.events:
            if event.kind == "red_flag.detected":
                codes += [str(c) for c in event.data.get("codes", [])]
            if event.kind not in _NO_RED_FLAG_SCAN:
                codes += codes_from_text(event.summary)
        red_flag = result_for_codes(codes)
        facts = [BriefFact(text=e.summary, event_ids=[e.id]) for e in record.events if e.kind in FACT_KINDS]
        return {
            "intake": intake,
            "red_flags": red_flag.flags,
            "facts": facts,
            "trace_attrs": {"event_count": len(record.events), "red_flag": red_flag.detected},
        }

    def _eligibility(self, state: CopilotState) -> dict:
        intake = state["intake"]
        result = evaluate(intake)
        record = state["record"]
        screened: set[str] = set()
        for e in record.events:
            if e.kind in {"reminder.done", "encounter.finalized"}:
                screened.update(str(c) for c in e.data.get("cancer_types", []))
        gaps: list[str] = []
        if intake.age is None:
            gaps.append("Thiếu tuổi.")
        if intake.gender is None:
            gaps.append("Thiếu giới tính.")
        questions: list[str] = []
        if state.get("red_flags"):
            gaps.append("Có dấu hiệu cảnh báo: ưu tiên đánh giá chẩn đoán; chưa soạn kế hoạch tầm soát định kỳ.")
            questions.append(
                "Thời điểm xuất hiện và diễn tiến của: "
                + ", ".join(f.symptom.lower() for f in state["red_flags"])
                + "?"
            )
        for s in result.suggestions:
            if s.cancer_type.value not in screened:
                gaps.append(f"Chưa ghi nhận lần tầm soát {LABEL_VI[s.cancer_type]} gần nhất (ngày, phương pháp).")
                questions.append(f"Lần tầm soát {LABEL_VI[s.cancer_type]} gần nhất là khi nào, bằng phương pháp gì?")
        if intake.smoking and intake.pack_years is None:
            gaps.append("Chưa có số gói-năm.")
            questions.append("Ước tính số gói-năm (số gói/ngày × số năm hút)?")
        if any(s.cancer_type == CancerType.lung for s in result.suggestions):
            questions.append("Hiện còn hút thuốc không? Nếu đã bỏ, cách đây bao nhiêu năm (tiêu chí ≤ 15 năm)?")
        for cancer_type in intake.family_history:
            if cancer_type != CancerType.other:
                questions.append(f"Người thân nào mắc {LABEL_VI[cancer_type]}, phát hiện ở tuổi nào?")
        if intake.hepatitis_b_or_c or intake.cirrhosis:
            questions.append("Tình trạng viêm gan/xơ gan hiện tại và lần đánh giá xơ hoá gan gần nhất?")
        return {
            "suggestions": result.suggestions,
            "risk_factors": result.risk_factors,
            "gaps": gaps,
            "questions": list(dict.fromkeys(questions))[:8],
            "trace_attrs": {"suggestion_count": len(result.suggestions), "gap_count": len(gaps)},
        }

    def _retrieve(self, state: CopilotState) -> dict:
        types = {s.cancer_type for s in state.get("suggestions", [])} | set(state["intake"].family_history)
        if not types:
            return {"sources": [], "trace_attrs": {"source_count": 0, "mode": "skipped"}}
        query = "tầm soát " + " ".join(LABEL_VI[t] for t in types) + " đối tượng ngoại lệ lưu ý"
        result = retrieve(query, gender=state["intake"].gender, cancer_types=types, dense=self.dense)
        return {
            "sources": result.sources,
            "trace_attrs": {"source_count": len(result.sources), "mode": result.mode, "dense": result.dense_status},
        }

    def _template_summary(self, state: CopilotState) -> str:
        record, intake = state["record"], state["intake"]
        who = ", ".join(
            x
            for x in [record.full_name, _GENDER_VI.get(intake.gender), f"{intake.age} tuổi" if intake.age else None]
            if x
        )
        parts = [f"Bệnh nhân {who}." if who else "Bệnh nhân chưa có đủ thông tin nhân khẩu."]
        if record.reason_for_visit:
            parts.append(f"Lý do khám: {record.reason_for_visit}")
        if state.get("red_flags"):
            parts.append("Có dấu hiệu cảnh báo: " + ", ".join(f.symptom.lower() for f in state["red_flags"]) + ".")
        if state.get("risk_factors"):
            reasons = [r for f in state["risk_factors"] for r in f.reasons]
            parts.append("Yếu tố nguy cơ ghi nhận: " + "; ".join(reasons).lower() + ".")
        if state.get("suggestions"):
            parts.append(
                "Guideline gợi ý: "
                + "; ".join(f"{LABEL_VI[s.cancer_type]} ({s.method})" for s in state["suggestions"])
                + "."
            )
        return " ".join(parts)

    def _draft_brief(self, state: CopilotState) -> dict:
        summary = self._template_summary(state)
        if not self.use_llm:
            return {"summary": summary, "trace_attrs": {"generator": "template"}}
        record = state["record"]
        known = {e.id for e in record.events}
        events = "\n".join(f"[{e.id}] {e.at:%Y-%m-%d} {e.kind}: {e.summary}" for e in record.events)
        suggestions_json = json.dumps(
            [s.model_dump(mode="json", exclude={"sources"}) for s in state.get("suggestions", [])], ensure_ascii=False
        )
        intake_json = json.dumps(state["intake"].model_dump(mode="json"), ensure_ascii=False)
        prompt = COPILOT_BRIEF_PROMPT.format(
            events=events or "(trống)",
            intake=intake_json,
            reason=record.reason_for_visit or "chưa ghi",
            suggestions=suggestions_json,
            gaps="\n".join(state.get("gaps", [])) or "không",
        )
        from ai_core.llm import get_chat_model

        try:
            model = get_chat_model().with_structured_output(_BriefDraft)
            draft = _BriefDraft.model_validate(
                model.invoke([SystemMessage(content=COPILOT_SYSTEM_PROMPT), HumanMessage(content=prompt)])
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("copilot_llm_unavailable trace_id=%s error_type=%s", state["trace_id"], type(exc).__name__)
            return {"summary": summary, "trace_attrs": {"generator": "template_fallback", "guard": "llm_error"}}
        evidence = [e.summary for e in record.events] + [intake_json, suggestions_json, record.reason_for_visit or ""]
        if (
            not draft.summary.strip()
            or unsafe_output(draft.summary)
            or ungrounded_numbers(draft.summary, evidence)
        ):
            return {"summary": summary, "trace_attrs": {"generator": "template_fallback", "guard": "summary_blocked"}}
        by_id = {e.id: e for e in record.events}
        llm_facts: list[BriefFact] = []
        for fact in draft.key_facts:
            cited = [i for i in dict.fromkeys(fact.event_ids) if i in known]
            # Mỗi con số trong fact phải có trong chính các mốc được trích (chống gán số bịa cho event có thật).
            fact_evidence = [f"{by_id[i].summary} {json.dumps(by_id[i].data, ensure_ascii=False)}" for i in cited]
            if cited and not unsafe_output(fact.text) and not ungrounded_numbers(fact.text, fact_evidence):
                llm_facts.append(BriefFact(text=fact.text, event_ids=cited))
        llm_questions = [
            q
            for q in draft.questions_to_clarify
            if q.strip() and not unsafe_output(q) and not ungrounded_numbers(q, evidence)
        ]
        dropped = len(draft.key_facts) - len(llm_facts)
        questions = list(dict.fromkeys([*llm_questions, *state.get("questions", [])]))[:8]
        return {
            "summary": draft.summary.strip(),
            "facts": llm_facts or state.get("facts", []),
            "questions": questions,
            "trace_attrs": {
                "generator": "llm",
                "guard": "pass",
                "facts_dropped": dropped,
                "questions_dropped": len(draft.questions_to_clarify) - len(llm_questions),
            },
        }

    def _draft_plan(self, state: CopilotState) -> dict:
        if state.get("red_flags"):
            return {"draft_plan": None, "trace_attrs": {"has_plan": False, "reason": "red_flag"}}
        items = [
            PlanItem(
                cancer_type=s.cancer_type,
                method=s.method,
                start_age=s.start_age,
                interval_months=s.interval_months,
                next_due=None,
                rationale=" ".join(x for x in [f"{s.applies_because}.", s.note] if x),
                sources=s.sources,
                priority=1 if s.elevated_risk else 2,
            )
            for s in state.get("suggestions", [])
            if s.interval_months
        ]
        if not items:
            return {"draft_plan": None, "trace_attrs": {"has_plan": False}}
        plan = validate_plan(
            ScreeningPlan(
                items=items,
                general_advice="Bác sĩ xác nhận ngày hẹn dựa trên lịch sử tầm soát trước khi phê duyệt.",
                generated_at=datetime.now(UTC),
                model=self.model_name,
            )
        )
        return {"draft_plan": plan, "trace_attrs": {"has_plan": True, "item_count": len(items)}}

    # ------------------------------------------------------------------ hỏi đáp

    def ask(self, question: str, record: PatientRecord, history: list[ChatTurn]) -> QuestionAnswer:
        trace_id = new_trace_id("copilot")
        if is_out_of_scope_request(question):
            return QuestionAnswer(
                answer=(
                    "Copilot không đưa ra chẩn đoán, không diễn giải kết quả cận lâm sàng và không tư vấn điều trị. "
                    "Có thể hỏi về guideline tầm soát hoặc dữ kiện trong hồ sơ."
                ),
                disclaimer=COPILOT_DISCLAIMER_VI,
                trace_id=trace_id,
                insufficient_evidence=True,
                trace_events=[{"node": "input_guard", "status": "ok", "out_of_scope": True}],
            )
        guideline = retrieve(question, dense=self.dense).sources
        candidates = guideline + record_sources(record)
        scores = BM25([tokenize(f"{s.title} {s.section} {s.excerpt}") for s in candidates]).scores(tokenize(question))
        ranked = [s for s, sc in sorted(zip(candidates, scores, strict=True), key=lambda x: -x[1]) if sc > 0][:6]
        events: list[dict] = [{"node": "retrieve", "status": "ok", "source_count": len(ranked)}]
        fallback = self._extractive_answer(ranked, trace_id, events)
        if not self.use_llm or not ranked:
            return fallback
        from ai_core.llm import get_chat_model

        allowed = {s.doc_id: s for s in ranked}
        prompt = COPILOT_QA_PROMPT.format(
            question=question,
            record=json.dumps([s.model_dump() for s in ranked if s.doc_id.startswith("record:")], ensure_ascii=False),
            sources=json.dumps(
                [s.model_dump() for s in ranked if not s.doc_id.startswith("record:")], ensure_ascii=False
            ),
            history=json.dumps([t.model_dump() for t in history[-8:]], ensure_ascii=False),
        )
        try:
            model = get_chat_model().with_structured_output(_AnswerDraft)
            draft = _AnswerDraft.model_validate(
                model.invoke([SystemMessage(content=COPILOT_SYSTEM_PROMPT), HumanMessage(content=prompt)])
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("copilot_qa_unavailable trace_id=%s error_type=%s", trace_id, type(exc).__name__)
            return fallback
        citations = [allowed[d] for d in dict.fromkeys(draft.source_ids) if d in allowed]
        evidence = [s.excerpt for s in ranked] + [question]
        if draft.insufficient_evidence:
            # LLM tự nhận thiếu căn cứ → trả căn cứ trích xuất (xác định), không dùng văn bản LLM.
            return fallback.model_copy(
                update={
                    "answer": "Chưa đủ căn cứ để trả lời chắc chắn câu hỏi này. " + fallback.answer,
                    "insufficient_evidence": True,
                    "trace_events": [*fallback.trace_events, {"node": "output_guard", "status": "insufficient"}],
                }
            )
        if (
            not draft.answer.strip()
            or unsafe_output(draft.answer)
            or not citations
            or ungrounded_numbers(draft.answer, evidence)
        ):
            fallback.trace_events.append({"node": "output_guard", "status": "blocked"})
            return fallback
        return QuestionAnswer(
            answer=draft.answer.strip(),
            sources=citations,
            disclaimer=COPILOT_DISCLAIMER_VI,
            trace_id=trace_id,
            insufficient_evidence=False,
            trace_events=[*events, {"node": "respond", "status": "ok", "generator": "llm", "cited": len(citations)}],
        )

    @staticmethod
    def _extractive_answer(ranked: list[Source], trace_id: str, events: list[dict]) -> QuestionAnswer:
        if not ranked:
            return QuestionAnswer(
                answer="Chưa tìm thấy căn cứ trong hồ sơ hoặc guideline hiện có cho câu hỏi này.",
                disclaimer=COPILOT_DISCLAIMER_VI,
                trace_id=trace_id,
                insufficient_evidence=True,
                trace_events=events,
            )
        lines = [f"• [{s.title} — {s.section}] {s.excerpt.splitlines()[0][:280]}" for s in ranked[:3]]
        return QuestionAnswer(
            answer="Các căn cứ liên quan nhất:\n" + "\n".join(lines),
            sources=ranked[:3],
            disclaimer=COPILOT_DISCLAIMER_VI,
            trace_id=trace_id,
            trace_events=[*events, {"node": "respond", "status": "ok", "generator": "extractive"}],
        )
