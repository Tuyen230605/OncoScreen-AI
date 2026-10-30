"""Hỏi đáp của bệnh nhân giới hạn ở kế hoạch đã được bác sĩ phê duyệt.

Câu hỏi có dấu hiệu cảnh báo (red-flag) → luôn trả lời khuyên khám sớm trước mọi thứ khác (S3), kể cả khi
chưa có kế hoạch; không bao giờ trả lời bằng lịch tầm soát định kỳ."""

from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ai_core.guardrails.disclaimer import DISCLAIMER_VI
from ai_core.guardrails.safety import is_out_of_scope_request, ungrounded_numbers, unsafe_output
from ai_core.observability import new_trace_id
from ai_core.prompts import PATIENT_QA_PROMPT, PATIENT_QA_SYSTEM_PROMPT
from ai_core.schemas import QuestionAnswer, ScreeningPlan, Source
from ai_core.text import fold
from ai_core.tools.red_flag_detector import detect_red_flags, urgent_guidance

logger = logging.getLogger(__name__)

NO_ANSWER = "Chưa đủ thông tin trong kế hoạch đã duyệt để trả lời câu hỏi này. Vui lòng trao đổi với bác sĩ."
_SYMPTOM_QUESTION = re.compile(r"trieu chung|chay mau|khoi u|u cuc|dau (o|vung)|\btoi (bi|mac|dang)\b")


class AnswerDraft(BaseModel):
    answer: str
    source_ids: list[str] = Field(default_factory=list)
    insufficient_evidence: bool = False


def needs_clinical_review(question: str) -> bool:
    return is_out_of_scope_request(question) or bool(_SYMPTOM_QUESTION.search(fold(question)))


def _fallback(trace_id: str, message: str = NO_ANSWER) -> QuestionAnswer:
    return QuestionAnswer(answer=message, disclaimer=DISCLAIMER_VI, trace_id=trace_id, insufficient_evidence=True)


def answer_question(question: str, plan: ScreeningPlan | None, use_llm: bool = True) -> QuestionAnswer:
    trace_id = new_trace_id("qa")
    red_flag = detect_red_flags([], question)
    if red_flag.detected:
        return QuestionAnswer(
            answer=urgent_guidance(red_flag),
            disclaimer=DISCLAIMER_VI,
            trace_id=trace_id,
            insufficient_evidence=True,
            trace_events=[{"node": "input_guard", "status": "ok", "red_flag": True}],
        )
    if plan is None or needs_clinical_review(question):
        return _fallback(trace_id)
    source_map: dict[str, Source] = {source.doc_id: source for item in plan.items for source in item.sources}
    if not source_map:
        return _fallback(trace_id)
    if not use_llm:
        lines = [f"• {item.method}: chu kỳ {item.interval_months} tháng. {item.rationale}" for item in plan.items]
        return QuestionAnswer(
            answer="Kế hoạch bác sĩ đã duyệt gồm:\n"
            + "\n".join(lines)
            + "\nHãy trao đổi với bác sĩ nếu cần giải thích thêm.",
            sources=list(source_map.values())[:3],
            disclaimer=DISCLAIMER_VI,
            trace_id=trace_id,
        )
    plan_json = json.dumps(plan.model_dump(mode="json"), ensure_ascii=False)
    prompt = PATIENT_QA_PROMPT.format(
        question=question,
        plan=plan_json,
        sources=json.dumps([s.model_dump(mode="json") for s in source_map.values()], ensure_ascii=False),
    )
    from ai_core.llm import get_chat_model

    try:
        model = get_chat_model().with_structured_output(AnswerDraft)
        draft = AnswerDraft.model_validate(
            model.invoke([SystemMessage(content=PATIENT_QA_SYSTEM_PROMPT), HumanMessage(content=prompt)])
        )
    except Exception as exc:  # noqa: BLE001 — không trả lời tự suy đoán khi LLM lỗi
        logger.warning("patient_qa_unavailable trace_id=%s error_type=%s", trace_id, type(exc).__name__)
        return _fallback(trace_id)
    citations = [source_map[doc_id] for doc_id in dict.fromkeys(draft.source_ids) if doc_id in source_map]
    evidence = [plan_json, question] + [s.excerpt for s in source_map.values()]
    if (
        draft.insufficient_evidence
        or not citations
        or not draft.answer.strip()
        or unsafe_output(draft.answer)
        or ungrounded_numbers(draft.answer, evidence)
    ):
        return _fallback(trace_id)
    return QuestionAnswer(answer=draft.answer.strip(), sources=citations, disclaimer=DISCLAIMER_VI, trace_id=trace_id)
