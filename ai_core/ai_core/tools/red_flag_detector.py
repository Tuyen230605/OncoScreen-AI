"""Tool: red-flag detector — RULE-BASED, chạy TRƯỚC mọi suy luận LLM (ràng buộc S3).

Nguồn rule: data/red_flags.json. Hai đường vào:
- câu trả lời bảng hỏi có question_id == code (vd. symptom_lump=true);
- văn bản tự do (chat, other_symptoms): so khớp pattern không dấu, bỏ qua câu phủ định ("không sờ thấy khối u")
  và mệnh đề có chủ ngữ là người thân ("mẹ tôi sờ thấy khối u" — được báo riêng qua `relative_codes_from_text`).
Cờ đã ghi nhận không bao giờ bị gỡ trong cùng phiên (fail-safe).
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache

from ai_core.config import DATA_DIR
from ai_core.schemas import Answer, RedFlag, RedFlagResult
from ai_core.text import fold, is_negated, subject_is_relative

_TRUTHY = {"true", "yes", "có", "co", "1"}
# Từ có dấu trùng dạng không dấu với triệu chứng: thay trước khi bỏ dấu ("vắng mặt" ≠ "vàng mắt").
_ACCENTED_HOMOGRAPHS = {"vắng mặt": "vang-mat"}

RED_FLAG_MESSAGE = (
    "Bạn có dấu hiệu cần được bác sĩ khám trực tiếp sớm. Hệ thống tạm dừng tư vấn tầm soát định kỳ "
    "để bạn ưu tiên đi khám. Điều này không có nghĩa là bạn mắc bệnh — chỉ là cần được đánh giá kỹ hơn."
)


@lru_cache(maxsize=1)
def _rules() -> dict[str, tuple[RedFlag, list[re.Pattern[str]]]]:
    raw = json.loads((DATA_DIR / "red_flags.json").read_text(encoding="utf-8"))
    return {r["code"]: (RedFlag.model_validate(r), [re.compile(p) for p in r.get("patterns", [])]) for r in raw}


def codes_from_answers(answers: list[Answer]) -> list[str]:
    rules = _rules()
    return [a.question_id for a in answers if a.question_id in rules and _is_truthy(a.value)]


def _prepare(text: str) -> str:
    low = unicodedata.normalize("NFC", text).casefold()
    for word, replacement in _ACCENTED_HOMOGRAPHS.items():
        low = low.replace(word, replacement)
    return fold(low)


def _scan(text: str) -> tuple[list[str], list[str]]:
    """(mã của chính người nói, mã chỉ xuất hiện ở người thân)."""
    folded = _prepare(text)
    own: list[str] = []
    relative: list[str] = []
    for code, (_, patterns) in _rules().items():
        hits = [m for pattern in patterns for m in pattern.finditer(folded) if not is_negated(folded, m.start())]
        if any(not subject_is_relative(folded, m.start()) for m in hits):
            own.append(code)
        elif hits:
            relative.append(code)
    return own, relative


def codes_from_text(text: str) -> list[str]:
    return _scan(text)[0]


def relative_codes_from_text(text: str) -> list[str]:
    """Dấu hiệu cảnh báo người dùng kể về NGƯỜI THÂN — không ngắt luồng của người dùng nhưng cần nhắc đi khám."""
    return _scan(text)[1]


def flags_for_codes(codes: list[str]) -> list[RedFlag]:
    rules = _rules()
    return [rules[c][0] for c in dict.fromkeys(codes) if c in rules]


def result_for_codes(codes: list[str]) -> RedFlagResult:
    flags = flags_for_codes(codes)
    if not flags:
        return RedFlagResult(detected=False)
    flags.sort(key=lambda f: 0 if f.severity.value == "urgent" else 1)
    return RedFlagResult(detected=True, flags=flags, message=RED_FLAG_MESSAGE)


def detect_red_flags(answers: list[Answer], text: str | None = None) -> RedFlagResult:
    codes = codes_from_answers(answers)
    for a in answers:
        if isinstance(a.value, str) and a.question_id not in _rules():
            codes += codes_from_text(a.value)
    if text:
        codes += codes_from_text(text)
    return result_for_codes(codes)


def urgent_guidance(result: RedFlagResult) -> str:
    """Lời khuyên khám sớm dùng chung (Navigator, hỏi đáp bệnh nhân)."""
    lines = [result.message or RED_FLAG_MESSAGE] + [f"• {f.symptom}: {f.advice}" for f in result.flags]
    lines.append(
        "Bạn có thể đặt lịch khám ưu tiên, hoặc đến cơ sở y tế gần nhất. "
        "Nếu triệu chứng nặng lên đột ngột, hãy gọi cấp cứu 115."
    )
    return "\n".join(lines)


def _is_truthy(v: object) -> bool:
    if isinstance(v, str):
        return unicodedata.normalize("NFC", v).strip().casefold() in _TRUTHY
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v == 1
    return v is True
