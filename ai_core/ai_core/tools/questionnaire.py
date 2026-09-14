"""Tool: risk-assessment questionnaire — đọc data/questionnaire.json, lọc theo hồ sơ, tính câu còn thiếu."""

from __future__ import annotations

import json
from functools import lru_cache

from ai_core.config import DATA_DIR
from ai_core.schemas import Answer, PatientProfile, Question, Questionnaire


@lru_cache(maxsize=1)
def _load() -> Questionnaire:
    raw = json.loads((DATA_DIR / "questionnaire.json").read_text(encoding="utf-8"))
    return Questionnaire.model_validate(raw)


def build_questionnaire(profile: PatientProfile) -> Questionnaire:
    """Bộ câu hỏi động: bỏ câu không áp dụng cho giới tính. TODO(Tuyền): lọc thêm theo tuổi."""
    q = _load()
    questions = [
        Question.model_validate(x.model_dump()) for x in q.questions if _applies_to_gender(x, profile.gender.value)
    ]
    return Questionnaire(version=q.version, questions=questions)


def _applies_to_gender(q: Question, gender: str) -> bool:
    # quy ước: id bắt đầu bằng "f_" chỉ hỏi nữ, "m_" chỉ hỏi nam
    if q.id.startswith("f_"):
        return gender == "female"
    if q.id.startswith("m_"):
        return gender == "male"
    return True


def _visible(q: Question, answered: dict[str, object]) -> bool:
    if not q.depends_on:
        return True
    key, _, expected = q.depends_on.partition("=")
    val = answered.get(key)
    return str(val).lower() == expected.lower()


def missing_required(profile: PatientProfile, answers: list[Answer]) -> list[str]:
    """question_id bắt buộc, đang hiển thị (theo depends_on) mà chưa trả lời."""
    answered = {a.question_id: a.value for a in answers}
    return [
        q.id
        for q in build_questionnaire(profile).questions
        if q.required and _visible(q, answered) and q.id not in answered
    ]
