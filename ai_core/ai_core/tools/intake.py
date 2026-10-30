"""Tool: intake — dựng IntakeProfile từ câu trả lời nhanh, văn bản tự do hoặc hồ sơ tài khoản.

Rule-based, chạy được không cần LLM. Chỉ ghi nhận điều người dùng nói về CHÍNH MÌNH: mệnh đề có chủ ngữ là người thân
("mẹ tôi bị viêm gan B", "chồng tôi hút thuốc") chỉ đóng góp vào tiền sử gia đình; câu hỏi chung chung
("Phụ nữ trên 21 tuổi có cần…", "Nam giới có cần…") không ghi đè tuổi/giới đã biết.
Mã red-flag chỉ cộng dồn.
"""

from __future__ import annotations

import math
import re
import unicodedata
from datetime import date

from ai_core.schemas import Answer, CancerType, Gender, IntakeProfile, PatientProfile
from ai_core.text import (
    FIRST_PERSON,
    KIN_SUBJECT,
    clause_after,
    clause_before,
    fold,
    is_negated,
    subject_is_relative,
)
from ai_core.tools.red_flag_detector import codes_from_answers, codes_from_text

_CANCER_WORDS: list[tuple[str, CancerType]] = [
    (r"vu", CancerType.breast),
    (r"co tu cung", CancerType.cervical),
    (r"(dai truc trang|dai trang|truc trang|ruot)", CancerType.colorectal),
    (r"gan", CancerType.liver),
    (r"phoi", CancerType.lung),
    (r"tuyen tien liet", CancerType.prostate),
]
_SELF_CANCER = re.compile(
    r"\b(da tung |tung |da |dang |vua )?(bi|mac|dieu tri) ung thu|\bduoc chan doan (la |bi |mac )?ung thu"
)
# Ngữ cảnh lo lắng / giả định / câu hỏi: "sợ bị ung thư", "nguy cơ mắc ung thư", "để phòng bị ung thư" ≠ đã mắc.
_NOT_A_DIAGNOSIS = re.compile(
    r"\b(so|lo|lo lang|ngai|nguy co|phong|phong ngua|phong tranh|tranh|kha nang|lieu|co the|neu|de|lam sao|"
    r"sau nay|bao gio|muon biet|co)\s*$"
    r"|\b(so|lo|lo lang|ngai|nguy co|phong ngua|phong tranh|kha nang|lieu|neu)\b"
)
_QUESTION_END = re.compile(r"\b(khong|ko|k|chua|chang|sao|gi)\s*$")
_NO_RELATIVE = re.compile(r"khong (ai|co ai)|chua (ai|co ai)")
_UNCERTAIN = re.compile(r"\b(khong biet|khong ro|chua biet|chua ro|lieu|co the|nghi)\b")
_SCREENING_CONTEXT = re.compile(
    r"\b(tiem|vac ?xin|vaccine|vacxin|chung ngua|ngua|phong|xet nghiem|kiem tra|tam soat|sang loc)\b[^,]{0,24}$"
)
_LABEL_TO_CANCER = {
    "ung thư vú": CancerType.breast,
    "ung thư cổ tử cung": CancerType.cervical,
    "ung thư đại trực tràng": CancerType.colorectal,
    "ung thư gan": CancerType.liver,
    "ung thư phổi": CancerType.lung,
    "ung thư tuyến tiền liệt": CancerType.prostate,
    "khác": CancerType.other,
}
_GENDER_LABEL = {
    "nữ": Gender.female,
    "nam": Gender.male,
    "khác": Gender.other,
    "female": Gender.female,
    "male": Gender.male,
    "other": Gender.other,
}


def _norm(value: str) -> str:
    """Chuẩn hoá NFC + chữ thường: giá trị "Nữ" dạng tổ hợp (NFD) vẫn khớp nhãn."""
    return unicodedata.normalize("NFC", value).strip().casefold()


def _as_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    if isinstance(value, str):
        v = _norm(value)
        if v in {"true", "yes", "có", "co", "1"}:
            return True
        if v in {"false", "no", "không", "khong", "0", "chưa", "chua"}:
            return False
    return None


def _as_float(value: object) -> float | None:
    """Số hữu hạn, không âm; giá trị khác (âm, nan, inf, chữ) bị bỏ qua thay vì làm hỏng IntakeProfile."""
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        number = float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


def from_answers(intake: IntakeProfile, answers: list[Answer]) -> IntakeProfile:
    data = intake.model_dump()
    for a in answers:
        qid, v = a.question_id, a.value
        if qid == "age" and (age := _as_float(v)) is not None and 0 <= age <= 120:
            data["age"] = int(age)
        elif qid == "gender" and isinstance(v, str) and _norm(v) in _GENDER_LABEL:
            data["gender"] = _GENDER_LABEL[_norm(v)]
        elif qid == "family_history":
            values = v if isinstance(v, (list, tuple)) else [v]
            types = [_LABEL_TO_CANCER[_norm(str(x))] for x in values if _norm(str(x)) in _LABEL_TO_CANCER]
            data["family_history"] = list(dict.fromkeys(types))
        elif qid == "personal_cancer_history" and (b := _as_bool(v)) is not None:
            data["personal_cancer_history"] = b
        elif qid == "smoking" and (b := _as_bool(v)) is not None:
            data["smoking"] = b
        elif qid == "pack_years" and (py := _as_float(v)) is not None:
            data["pack_years"] = py
        elif qid == "hbv_hcv" and (b := _as_bool(v)) is not None:
            data["hepatitis_b_or_c"] = b
        elif qid == "cirrhosis" and (b := _as_bool(v)) is not None:
            data["cirrhosis"] = b
        elif qid == "hpv_vaccine" and (b := _as_bool(v)) is not None:
            data["hpv_vaccinated"] = b
    data["symptom_codes"] = list(dict.fromkeys([*intake.symptom_codes, *codes_from_answers(answers)]))
    for a in answers:
        if a.question_id == "other_symptoms" and isinstance(a.value, str):
            data["symptom_codes"] = list(dict.fromkeys([*data["symptom_codes"], *codes_from_text(a.value)]))
    return IntakeProfile.model_validate(data)


# ----------------------------------------------------------------------------------------------- văn bản tự do

# Từ đứng ngay trước con số chỉ mốc/khoảng thời gian, không phải tuổi hiện tại ("từ 45 tuổi", "lúc 20 tuổi").
_AGE_TIME_MARKER = re.compile(r"\b(tu|den|toi tu|khi|luc|truoc|sau|duoi|qua|moc|o do|cho)\s*$")
# Từ chỉ tuổi xấp xỉ: chỉ tính khi chính người nói là chủ ngữ ("tôi ngoài 50 tuổi"), không tính "phụ nữ trên 21 tuổi".
_AGE_APPROX = re.compile(r"\b(tren|ngoai|hon|tam|khoang|gan)\s*$")
_GENERIC_SUBJECT = re.compile(r"\b(phu nu|nam gioi|nu gioi|dan ong|moi nguoi|nguoi|ai|benh nhan|tre em|chi em)\b")


def _speaker_is_subject(folded: str, start: int) -> bool:
    """Người nói là chủ ngữ tường minh của mệnh đề ("tôi…", "mình…") và không phải sở hữu của người thân."""
    before = clause_before(folded, start)
    kin_spans = [m.span() for m in KIN_SUBJECT.finditer(before)]
    return any(not any(a <= m.start() < b for a, b in kin_spans) for m in FIRST_PERSON.finditer(before))


def _age(folded: str, today: date) -> tuple[int | None, bool]:
    """(tuổi, tường_minh). Tường minh = người nói tự nêu ("tôi 45 tuổi") → được ghi đè giá trị cũ."""
    for m in re.finditer(r"\b(\d{1,3})\s*(tuoi|t)\b", folded):
        if subject_is_relative(folded, m.start()):  # "mẹ tôi 70 tuổi", "bố mất năm 60 tuổi"
            continue
        before = clause_before(folded, m.start())
        explicit = _speaker_is_subject(folded, m.start())
        if _AGE_TIME_MARKER.search(before):  # "bắt đầu từ 45 tuổi", "hút thuốc từ lúc 20 tuổi"
            continue
        if not explicit and (_AGE_APPROX.search(before) or _GENERIC_SUBJECT.search(before)):
            continue  # "Phụ nữ trên 21 tuổi có cần…"
        return int(m.group(1)), explicit
    if (m := re.search(r"sinh nam (19\d\d|20\d\d)", folded)) and not subject_is_relative(folded, m.start()):
        return today.year - int(m.group(1)), True
    if (m := re.search(r"nam nay (\d{1,3})\b", folded)) and not subject_is_relative(folded, m.start()):
        return int(m.group(1)), _speaker_is_subject(folded, m.start())
    return None, False


_KIN_BEFORE_PRONOUN = re.compile(
    r"\b(con|vo|chong|me|bo|cha|chi|anh|em|co|di|chu|bac|ong|ba|cau|mo|nha)\s*$"
)
_GENDER_ACCENTED = [
    # (pattern, gender, explicit)
    (r"\b(tôi|em|mình|tui)\s+(là\s+)?(nữ|phụ nữ|con gái)\b", Gender.female, True),
    (r"\b(tôi|em|mình|tui)\s+(là\s+)?(nam|đàn ông|con trai|nam giới)\b", Gender.male, True),
    (r"giới tính\s*:?\s*nữ\b", Gender.female, True),
    (r"giới tính\s*:?\s*nam\b", Gender.male, True),
    (r"\bnữ\s*,?\s*\d{1,3}\s*(tuổi|t)\b|\d{1,3}\s*(tuổi|t)\s*,?\s*nữ\b", Gender.female, False),
    (r"\bnam\s*,?\s*\d{1,3}\s*(tuổi|t)\b|\d{1,3}\s*(tuổi|t)\s*,?\s*nam\b", Gender.male, False),
]
_GENDER_UNACCENTED = [
    (r"\b(toi|em|minh|tui)\s+(la\s+)?(nu|phu nu|con gai)\b", Gender.female, True),
    (r"\b(toi|em|minh|tui)\s+(la\s+)?(nam|dan ong|con trai|nam gioi)\b(?!\s+nay)", Gender.male, True),
    (r"gioi tinh\s*:?\s*nu\b", Gender.female, True),
    (r"gioi tinh\s*:?\s*nam\b", Gender.male, True),
    (r"\bnu\s*,?\s*\d{1,3}\s*(tuoi|t)\b|\d{1,3}\s*(tuoi|t)\s*,?\s*nu\b", Gender.female, False),
    (r"\bnam\s*,?\s*\d{1,3}\s*(tuoi|t)\b|\d{1,3}\s*(tuoi|t)\s*,?\s*nam\b", Gender.male, False),
]


def _gender(text: str, folded: str) -> tuple[Gender | None, bool]:
    """(giới, tường_minh). Dạng có dấu phân biệt "nam"/"năm"; văn bản gõ không dấu dùng mẫu không dấu.
    Không suy giới từ câu hỏi chung ("Nam giới có cần tầm soát…") hay từ người thân ("con tôi là con trai")."""
    low = re.sub(r"\s+", " ", unicodedata.normalize("NFC", text).casefold()).strip()
    candidates = [(low, _GENDER_ACCENTED)]
    if folded == low:  # người dùng gõ không dấu
        candidates.append((folded, _GENDER_UNACCENTED))
    for explicit_pass in (True, False):
        for source, patterns in candidates:
            for pattern, gender, explicit in patterns:
                if explicit != explicit_pass:
                    continue
                for m in re.finditer(pattern, source):
                    if _KIN_BEFORE_PRONOUN.search(fold(source[max(0, m.start() - 24) : m.start()])):
                        continue
                    return gender, explicit
    return None, False


def _personal_history(folded: str) -> bool | None:
    """True: người nói kể đã/đang mắc ung thư; False: phủ định rõ ("tôi chưa từng bị ung thư"); None: không nói.
    "Tôi sợ bị ung thư", "tôi có nguy cơ mắc ung thư không?", "tôi có bị ung thư vú không?" → None."""
    result: bool | None = None
    for m in _SELF_CANCER.finditer(folded):
        if subject_is_relative(folded, m.start()):
            continue
        before = clause_before(folded, m.start())
        if before.strip() and not _speaker_is_subject(folded, m.start()):
            continue  # chủ ngữ không phải người nói ("phụ nữ bị ung thư vú…")
        if is_negated(folded, m.start()):
            result = False if result is None else result
            continue
        if _NOT_A_DIAGNOSIS.search(before) or _QUESTION_END.search(clause_after(folded, m.end())):
            continue
        return True
    return result


def _family_history(folded: str, existing: list[CancerType]) -> list[CancerType]:
    family = list(existing)
    for word, cancer_type in _CANCER_WORDS:
        for m in re.finditer(rf"ung thu {word}\b", folded):
            if not subject_is_relative(folded, m.start()) or is_negated(folded, m.start()):
                continue
            if _NO_RELATIVE.search(clause_before(folded, m.start())):
                continue
            if cancer_type not in family:
                family.append(cancer_type)
    return family


def _self_matches(pattern: str, folded: str) -> list[re.Match[str]]:
    return [m for m in re.finditer(pattern, folded) if not subject_is_relative(folded, m.start())]


def _smoking(folded: str, today: date) -> tuple[bool | None, float | None]:
    """(đang hút hoặc bỏ ≤ 15 năm — cùng nghĩa câu hỏi `smoking` của bảng hỏi, số gói-năm)."""
    smoking: bool | None = None
    if _self_matches(r"\b(khong|chua tung|chua bao gio|chua he|khong he|ko)\s+hut thuoc", folded):
        smoking = False
    elif any(
        not re.match(r"\s*thu dong", folded[m.end() :])
        for m in _self_matches(r"hut thuoc|nghien thuoc|bo thuoc la|bo hut thuoc|cai thuoc", folded)
    ):
        smoking = True
        quit_years: int | None = None
        for m in _self_matches(
            r"(bo|cai)( hut)? thuoc( la)?(?: (?:duoc|da|tu|cach day|khoang|hon|gan|roi|ca))* (\d{1,2})\s*nam", folded
        ):
            quit_years = int(m.group(4))
        for m in _self_matches(r"(bo|cai)( hut)? thuoc( la)?(?: \w+){0,3} tu nam (19\d\d|20\d\d)", folded):
            quit_years = today.year - int(m.group(4))
        if quit_years is not None and quit_years > 15:
            smoking = False  # bỏ thuốc > 15 năm: ngoài tiêu chí "còn hút hoặc bỏ dưới 15 năm"

    pack_years: float | None = None
    if m := next(iter(_self_matches(r"(\d+(?:[.,]\d+)?)\s*goi[- ]?nam", folded)), None):
        pack_years = _as_float(m.group(1))
    elif m := next(
        iter(
            _self_matches(r"(\d+(?:[.,]\d+)?)\s*goi\s*(?:moi |/ ?|mot |1 )?ngay\D{0,30}?(\d+)\s*nam", folded)
        ),
        None,
    ):
        pack_years = (_as_float(m.group(1)) or 0) * int(m.group(2))
    return smoking, pack_years


def _condition(pattern: str, folded: str, *, screening_context: bool = False) -> bool | None:
    """Tình trạng của chính người nói: True/False (phủ định); None nếu chỉ nói về người thân, tiêm phòng,
    xét nghiệm âm tính hoặc không chắc chắn."""
    for m in _self_matches(pattern, folded):
        before, after = clause_before(folded, m.start()), clause_after(folded, m.end())
        if screening_context and (_SCREENING_CONTEXT.search(before) or re.match(r"(\s+\w+){0,2}\s+am tinh", after)):
            continue
        if _UNCERTAIN.search(before) or _QUESTION_END.search(after):
            continue
        return not is_negated(folded, m.start())
    return None


def from_text(intake: IntakeProfile, text: str, today: date | None = None) -> IntakeProfile:
    today = today or date.today()
    folded = fold(text)
    data = intake.model_dump()
    age, explicit_age = _age(folded, today)
    if age is not None and 0 < age <= 110 and (explicit_age or intake.age is None):
        data["age"] = age
    gender, explicit_gender = _gender(text, folded)
    if gender is not None and (explicit_gender or intake.gender is None):
        data["gender"] = gender

    if (personal := _personal_history(folded)) is not None:
        data["personal_cancer_history"] = personal
    data["family_history"] = _family_history(folded, list(intake.family_history))

    smoking, pack_years = _smoking(folded, today)
    if smoking is not None:
        data["smoking"] = smoking
    if pack_years is not None:
        data["pack_years"] = pack_years

    if (hep := _condition(r"viem gan (b|c)\b", folded, screening_context=True)) is not None:
        data["hepatitis_b_or_c"] = hep
    if (cirrhosis := _condition(r"xo gan", folded)) is not None:
        data["cirrhosis"] = cirrhosis
    if (hpv := _condition(r"tiem (vac ?xin |vaccine |vacxin |phong )?hpv", folded)) is not None:
        data["hpv_vaccinated"] = hpv

    data["symptom_codes"] = list(dict.fromkeys([*intake.symptom_codes, *codes_from_text(text)]))
    return IntakeProfile.model_validate(data)


def from_profile(profile: PatientProfile) -> IntakeProfile:
    """Hồ sơ tài khoản → IntakeProfile (genetics_history dạng mã `breast_cancer_mother`)."""
    family = [
        cancer_type
        for cancer_type in CancerType
        if cancer_type != CancerType.other
        and any(code.startswith(f"{cancer_type.value}_") for code in profile.genetics_history)
    ]
    lifestyle = profile.lifestyle or {}
    return IntakeProfile(
        age=profile.age,
        gender=profile.gender,
        family_history=family,
        smoking=_as_bool(lifestyle.get("smoking")),
        pack_years=_as_float(lifestyle.get("pack_years")),
        hepatitis_b_or_c=_as_bool(lifestyle.get("hepatitis_b_or_c")),
        cirrhosis=_as_bool(lifestyle.get("cirrhosis")),
    )


def merge(primary: IntakeProfile | None, secondary: IntakeProfile | None) -> IntakeProfile:
    """Ưu tiên `primary`, điền chỗ trống từ `secondary`; danh sách được hợp lại."""
    if primary is None:
        return secondary or IntakeProfile()
    if secondary is None:
        return primary
    a, b = primary.model_dump(), secondary.model_dump()
    out = {k: (a[k] if a[k] is not None else b[k]) for k in a}
    out["family_history"] = list(dict.fromkeys([*a["family_history"], *b["family_history"]]))
    out["symptom_codes"] = list(dict.fromkeys([*a["symptom_codes"], *b["symptom_codes"]]))
    return IntakeProfile.model_validate(out)


def to_genetics_codes(intake: IntakeProfile) -> list[str]:
    """IntakeProfile → mã genetics_history cho patient_profiles khi tài khoản được tạo từ phiên tư vấn."""
    return [f"{c.value}_cancer_family" for c in intake.family_history if c != CancerType.other]


def missing_info(intake: IntakeProfile) -> list[str]:
    missing = [name for name in ("age", "gender") if getattr(intake, name) is None]
    if intake.smoking and intake.pack_years is None and (intake.age or 0) >= 50:
        missing.append("pack_years")
    return missing
