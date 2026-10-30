"""Cầu nối duy nhất tới ai_core. Mọi lời gọi AI đi qua đây (threadpool + map lỗi → 502 + ghi agent_runs)."""

from __future__ import annotations

import logging
from functools import partial
from time import monotonic

from ai_core.api import AgentError, get_agent, list_services
from ai_core.schemas import (
    Answer,
    CancerType,
    ChatTurn,
    ClinicalBrief,
    EducationContent,
    IntakeProfile,
    NavigatorReply,
    PatientRecord,
    QuestionAnswer,
    Questionnaire,
    ScreeningPlan,
)
from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AgentRun

__all__ = ["agent_name", "list_services"]

log = logging.getLogger(__name__)


def _agent():
    return get_agent(force_mock=settings.use_mock_agent)


def agent_name() -> str:
    return _agent().name


async def _call(fn, *args, **kwargs):
    try:
        return await run_in_threadpool(partial(fn, *args, **kwargs))
    except AgentError as exc:
        # Chi tiết lỗi (có thể chứa dữ liệu đầu vào) chỉ ghi log, không trả về client.
        log.exception("AI Core lỗi khi gọi %s", getattr(fn, "__name__", fn))
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Trợ lý AI tạm thời không xử lý được yêu cầu. Vui lòng thử lại sau."
        ) from exc


def _generator(events: list[dict]) -> str | None:
    for event in reversed(events):
        if "generator" in event:
            return str(event["generator"])
    return None


def record_run(
    db: Session,
    agent: str,
    *,
    trace_id: str,
    events: list[dict],
    started: float,
    patient_id: str | None = None,
    consultation_id: str | None = None,
    encounter_id: str | None = None,
    red_flag: bool = False,
    next_action: str | None = None,
    insufficient_evidence: bool = False,
) -> None:
    generator = _generator(events)
    db.add(
        AgentRun(
            agent=agent,
            trace_id=trace_id,
            patient_id=patient_id,
            consultation_id=consultation_id,
            encounter_id=encounter_id,
            latency_ms=round((monotonic() - started) * 1000, 1),
            generator=generator,
            red_flag=red_flag,
            next_action=next_action,
            insufficient_evidence=insufficient_evidence,
            guard_blocked=bool(generator and "fallback" in generator)
            or any(e.get("status") == "blocked" for e in events),
            events=events,
        )
    )


def navigator_questionnaire() -> Questionnaire:
    return _agent().navigator_questionnaire()


async def navigate(
    message: str | None, answers: list[Answer], intake: IntakeProfile, history: list[ChatTurn]
) -> NavigatorReply:
    return await _call(_agent().navigate, message=message, answers=answers, intake=intake, history=history)


async def build_brief(record: PatientRecord) -> ClinicalBrief:
    return await _call(_agent().build_brief, record)


async def ask_copilot(question: str, record: PatientRecord, history: list[ChatTurn]) -> QuestionAnswer:
    return await _call(_agent().ask_copilot, question, record, history)


async def answer_question(question: str, approved_plan: ScreeningPlan | None) -> QuestionAnswer:
    return await _call(_agent().answer_question, question, approved_plan)


async def get_education(cancer_type: CancerType) -> EducationContent:
    return await _call(_agent().get_education, cancer_type)
