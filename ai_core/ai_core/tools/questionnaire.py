"""Tool: risk-assessment questionnaire — đọc data/questionnaire.json, lọc theo hồ sơ, tính câu còn thiếu."""

from __future__ import annotations

import json
from functools import lru_cache

from ai_core.config import DATA_DIR
from ai_core.schemas import Answer, PatientProfile, Question, Questionnaire


@lru_cache(maxsize=1)
def _load() -> Questionnaire:
    raw = json.loads((DATA_DIR / "questionnaire.json").read_text(encoding="utf-8"))
    questionnaire = Questionnaire.model_validate(raw)
    _validate_questionnaire(questionnaire)
    return questionnaire


def _validate_questionnaire(questionnaire: Questionnaire) -> None:
    """Fail early when IDs or conditional visibility rules are inconsistent."""
    question_ids = [question.id for question in questionnaire.questions]
    known_ids = set(question_ids)
    if len(known_ids) != len(question_ids):
        raise ValueError("questionnaire contains duplicate question IDs")

    for question in questionnaire.questions:
        if not question.depends_on:
            continue
        parent_id, separator, expected = question.depends_on.partition("=")
        parent_id = parent_id.strip()
        if not separator or not parent_id or not expected.strip():
            raise ValueError(f"invalid depends_on for question {question.id!r}: {question.depends_on!r}")
        if parent_id not in known_ids:
            raise ValueError(f"question {question.id!r} depends on unknown question {parent_id!r}")
        if parent_id == question.id:
            raise ValueError(f"question {question.id!r} cannot depend on itself")


def build_questionnaire(profile: PatientProfile) -> Questionnaire:
    """Return the questionnaire questions that apply to the patient's gender."""
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
    expected_normalized = expected.strip().casefold()
    if isinstance(val, (list, tuple, set)):
        return any(str(option).strip().casefold() == expected_normalized for option in val)
    if isinstance(val, bool):
        return str(val).casefold() == expected_normalized
    return val is not None and str(val).strip().casefold() == expected_normalized


def missing_required(profile: PatientProfile, answers: list[Answer]) -> list[str]:
    """question_id bắt buộc, đang hiển thị (theo depends_on) mà chưa trả lời."""
    answered = {a.question_id: a.value for a in answers}
    return [
        q.id
        for q in build_questionnaire(profile).questions
        if q.required and _visible(q, answered) and q.id not in answered
    ]
