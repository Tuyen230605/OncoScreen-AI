"""Cầu nối duy nhất tới ai_core. Mọi lời gọi AI đi qua đây (threadpool + map lỗi → 502)."""

from __future__ import annotations

from ai_core.api import AgentError, get_agent
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
from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.config import settings


def _agent():
    return get_agent(force_mock=settings.use_mock_agent)


def agent_name() -> str:
    return _agent().name


async def _call(fn, *args):
    try:
        return await run_in_threadpool(fn, *args)
    except AgentError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"AI Core lỗi: {exc}") from exc


async def get_questionnaire(profile: PatientProfile) -> Questionnaire:
    return await _call(_agent().get_questionnaire, profile)


async def check_red_flags(answers: list[Answer]) -> RedFlagResult:
    return await _call(_agent().check_red_flags, answers)


async def missing_questions(profile: PatientProfile, answers: list[Answer]) -> list[str]:
    return await _call(_agent().missing_questions, profile, answers)


async def run_screening(ctx: PatientContext) -> ScreeningResult:
    return await _call(_agent().run_screening, ctx)


async def get_education(cancer_type: CancerType) -> EducationContent:
    return await _call(_agent().get_education, cancer_type)
