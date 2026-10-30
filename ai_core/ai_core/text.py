"""Chuẩn hoá văn bản tiếng Việt cho rule-based matching và tìm kiếm từ khoá.

Người dùng có thể gõ có dấu hoặc không dấu; mọi pattern rule-based được viết ở dạng không dấu và so khớp trên `fold()`.
"""

from __future__ import annotations

import re
import unicodedata

_SPACES = re.compile(r"\s+")
# Từ phủ định đứng ngay trước, hoặc cách đúng một từ "chi phối" động từ triệu chứng ("không bị", "không có",
# "chưa thấy"). Không coi "không biết/không những/không rõ… <triệu chứng>" là phủ định triệu chứng.
_NEGATION_BEFORE = re.compile(
    r"\b(khong he|khong co|chua tung|chua bao gio|khong|chua|chang|ko|k)\s+"
    r"((co|bi|thay|mac|gap|tung|duoc|di|so|so thay|nhin thay|phat hien|thay co|co bi)\s+)?$"
)
_CLAUSE_SPLIT = re.compile(r"[,.;:!?\n()]+")
_CLAUSE_WINDOW = 160

# Chủ ngữ là người thân. Từ không nhập nhằng được tính khi đứng một mình ("mẹ bị…", "bố mất năm 60 tuổi");
# từ nhập nhằng (cô/có, bà/ba, đi/dì, con, chồng/chống…) và các xưng hô có thể là chính người nói ("chị 45 tuổi")
# chỉ tính khi kèm đại từ sở hữu ("cô tôi", "chồng tôi", "con gái tôi").
# "bỏ/bộ" cũng gấp thành "bo" ("bỏ thuốc", "bỏ hút thuốc", "toàn bộ") nên bị loại trừ.
_KIN_WORDS = (
    r"bo|me|cha|ba|ong|co|di|chu|bac|cau|mo|thim|anh|chi|em|con|vo|chong|nha|ba ngoai|ba noi|ong ngoai|ong noi|"
    r"anh trai|chi gai|em gai|em trai|con gai|con trai|anh ruot|chi ruot|em ruot"
)
_POSSESSIVE = r"\s+(?:cua\s+)?(?:toi|minh|tui|em)\b"
_UNAMBIGUOUS_KIN = (
    r"bo(?! (?:thuoc|hut|ruou|bia|y te|doi|phan))|me|cha|ba ngoai|ba noi|ong ngoai|ong noi|anh trai|chi gai|em gai|"
    r"em trai|nguoi than|nguoi nha|trong nha|bo me|cha me|ba me|ong ba|anh chi em|ho hang|gia dinh"
)
KIN_SUBJECT = re.compile(
    rf"\b(?<!toan )(?:(?:{_UNAMBIGUOUS_KIN})\b(?:{_POSSESSIVE})?|(?:{_KIN_WORDS}){_POSSESSIVE})"
)
FIRST_PERSON = re.compile(r"\b(toi|minh|tui|em)\b")


def fold(text: str) -> str:
    """Bỏ dấu, bỏ ký tự vô hình (zero-width…), chữ thường, gộp khoảng trắng: "Sờ thấy KHỐI u" → "so thay khoi u"."""
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) not in {"Mn", "Cf"})
    return _SPACES.sub(" ", stripped.casefold()).strip()


def is_negated(folded: str, start: int, window: int = 24) -> bool:
    """True nếu ngay trước vị trí `start` có từ phủ định ("không sờ thấy khối u", "không bị ho ra máu",
    "chưa thấy có cục"); "không biết đi ngoài ra máu…", "không những ho ra máu…" KHÔNG phải phủ định."""
    return bool(_NEGATION_BEFORE.search(folded[max(0, start - window) : start] + " ")) if start else False


def sentences(folded: str) -> list[str]:
    return [part.strip() for part in re.split(r"[.;!?\n]+", folded) if part.strip()]


def clause_before(folded: str, start: int) -> str:
    """Phần mệnh đề (tách theo dấu câu) đứng trước vị trí `start`, tối đa `_CLAUSE_WINDOW` ký tự
    (giới hạn để tin nhắn rất dài không làm chi phí tăng bậc hai)."""
    lo = max(0, start - _CLAUSE_WINDOW)
    head = folded[lo:start]
    if lo:  # bỏ từ bị cắt dở ở đầu cửa sổ
        head = head.split(" ", 1)[1] if " " in head else ""
    return _CLAUSE_SPLIT.split(head)[-1]


def subject_is_relative(folded: str, start: int) -> bool:
    """True nếu chủ ngữ gần nhất trước `start` trong cùng mệnh đề là người thân ("mẹ tôi sờ thấy khối u",
    "chồng tôi hút thuốc"); False nếu là chính người nói hoặc không rõ ("tôi…", "mẹ tôi khoẻ nhưng tôi…").

    Không rõ chủ ngữ → coi là bản thân (an toàn cho red-flag)."""
    before = clause_before(folded, start)
    kin_spans = [m.span() for m in KIN_SUBJECT.finditer(before)]
    if not kin_spans:
        return False
    last_kin = kin_spans[-1][1]
    for m in FIRST_PERSON.finditer(before):
        inside_kin = any(a <= m.start() < b for a, b in kin_spans)
        if not inside_kin and m.start() >= last_kin:
            return False
    return True


def clause_after(folded: str, end: int) -> str:
    """Phần mệnh đề (tách theo dấu câu) đứng sau vị trí `end`."""
    return _CLAUSE_SPLIT.split(folded[end : end + _CLAUSE_WINDOW])[0]
