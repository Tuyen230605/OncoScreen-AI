"""Request/response của Navigator (công khai) — mirror API_CONTRACT §1."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Literal

from ai_core.schemas import Answer, CancerType, IntakeProfile, NavigatorReply
from pydantic import BaseModel, Field, field_validator, model_validator

# Câu hỏi dạng số trong bảng hỏi nhanh (ai_core/data/questionnaire.json): giá trị đọc được thành số phải hữu hạn, ≥ 0
NUMBER_QUESTION_IDS = ("age", "pack_years")


class NavigatorMessageIn(BaseModel):
    message: str | None = Field(default=None, max_length=2000)
    answers: list[Answer] = Field(default_factory=list, max_length=40)

    @field_validator("answers")
    @classmethod
    def _non_negative_numbers(cls, answers: list[Answer]) -> list[Answer]:
        for a in answers:
            if a.question_id not in NUMBER_QUESTION_IDS or a.value in (None, "") or isinstance(a.value, bool):
                continue
            try:
                number = float(str(a.value).replace(",", "."))
            except ValueError:
                continue  # không đọc được thành số → AI Core bỏ qua như câu chưa trả lời
            if not math.isfinite(number) or number < 0:
                raise ValueError(f"Câu trả lời '{a.question_id}' phải là số không âm")
        return answers

    @model_validator(mode="after")
    def _not_empty(self) -> NavigatorMessageIn:
        if not (self.message and self.message.strip()) and not self.answers:
            raise ValueError("Cần message hoặc answers")
        return self


class ConsultMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    at: datetime


class ConsultationOut(BaseModel):
    id: str
    linked: bool
    intake: IntakeProfile
    messages: list[ConsultMessage] = Field(default_factory=list)
    last_reply: NavigatorReply | None = None
    created_at: datetime
    updated_at: datetime


class ConsultationCreated(BaseModel):
    access_token: str
    consultation: ConsultationOut


class ServiceOut(BaseModel):
    code: str
    name: str
    description: str
    cancer_types: list[CancerType]
