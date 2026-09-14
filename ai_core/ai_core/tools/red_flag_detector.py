"""Tool: red-flag detector — RULE-BASED, chạy TRƯỚC mọi suy luận LLM (ràng buộc S3).

Nguồn rule: data/red_flags.json. Câu hỏi triệu chứng trong questionnaire có id == code ở đây.
"""

from __future__ import annotations

import json
from functools import lru_cache

from ai_core.config import DATA_DIR
from ai_core.schemas import Answer, RedFlag, RedFlagResult

_TRUTHY = {True, "true", "yes", "có", "co", "1"}


@lru_cache(maxsize=1)
def _rules() -> dict[str, RedFlag]:
    raw = json.loads((DATA_DIR / "red_flags.json").read_text(encoding="utf-8"))
    return {r["code"]: RedFlag.model_validate(r) for r in raw}


def detect_red_flags(answers: list[Answer]) -> RedFlagResult:
    rules = _rules()
    flags: list[RedFlag] = []
    for a in answers:
        if a.question_id in rules and _is_truthy(a.value):
            flags.append(rules[a.question_id])
        # TODO(Tuyền): với câu text tự do (question_id == "other_symptoms"), quét từ khoá / dùng LLM
        # NHƯNG LLM chỉ được THÊM cờ, không được bỏ cờ rule-based.
    if not flags:
        return RedFlagResult(detected=False)
    flags.sort(key=lambda f: 0 if f.severity.value == "urgent" else 1)
    return RedFlagResult(
        detected=True,
        flags=flags,
        message=(
            "Bạn có dấu hiệu cần được bác sĩ khám trực tiếp sớm. Hệ thống tạm dừng tư vấn tầm soát định kỳ "
            "để bạn ưu tiên đi khám chuyên khoa. Điều này không có nghĩa là bạn mắc bệnh — "
            "chỉ là cần được đánh giá kỹ hơn."
        ),
    )


def _is_truthy(v: object) -> bool:
    if isinstance(v, str):
        return v.strip().lower() in _TRUTHY
    return v in _TRUTHY
