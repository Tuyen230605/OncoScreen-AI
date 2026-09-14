"""Guardrail an toàn: chặn từ ngữ chẩn đoán (S1), chặn item không nguồn (S2).

Dùng ở node `guardrail` và có thể dùng lại ở backend nếu bác sĩ sửa plan.
"""

from __future__ import annotations

import re

from ai_core.schemas import ScreeningPlan

# TODO(Tuyền): mở rộng danh sách; cân nhắc false-positive ("không bị" là hợp lệ?)
_DIAGNOSIS_PATTERNS = [
    r"\bbạn (đã |đang )?(bị|mắc)\b",
    r"\bchẩn đoán (là|bạn)\b",
    r"\bkết luận (bạn|là)\b.*ung thư",
    r"\byou (have|are diagnosed)\b",
]
_RE = re.compile("|".join(_DIAGNOSIS_PATTERNS), re.IGNORECASE)


class GuardrailViolation(Exception):
    pass


def find_diagnosis_language(text: str) -> list[str]:
    return [m.group(0) for m in _RE.finditer(text)]


def validate_plan(plan: ScreeningPlan) -> ScreeningPlan:
    """Raise GuardrailViolation nếu vi phạm; trả lại plan nếu ổn."""
    problems: list[str] = []
    for i, item in enumerate(plan.items):
        if not item.sources:
            problems.append(f"item[{i}] không có nguồn")
        for hit in find_diagnosis_language(item.rationale):
            problems.append(f"item[{i}].rationale chứa ngôn ngữ chẩn đoán: {hit!r}")
    for hit in find_diagnosis_language(plan.general_advice):
        problems.append(f"general_advice chứa ngôn ngữ chẩn đoán: {hit!r}")
    if problems:
        raise GuardrailViolation("; ".join(problems))
    return plan
