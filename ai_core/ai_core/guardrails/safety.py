"""Guardrail an toàn đầu vào/đầu ra.

Đầu vào: nhận diện yêu cầu chẩn đoán/diễn giải kết quả/điều trị (ngoài phạm vi), dấu hiệu prompt injection.
Đầu ra: chặn ngôn ngữ chẩn đoán (S1), lời khuyên điều trị (S1), item không nguồn (S2), con số không có trong bằng chứng
(chống bịa mốc tuổi/chu kỳ). Mọi pattern so khớp trên văn bản đã bỏ dấu → bắt được cả câu gõ không dấu.
Dùng ở các agent và ở backend khi bác sĩ sửa plan.
"""

from __future__ import annotations

import re
import unicodedata

from ai_core.schemas import ScreeningPlan
from ai_core.text import fold

_SPACES = re.compile(r"\s+")
_CANCER_SITE = (
    r"( (vu|gan|phoi|co tu cung|tu cung|dai trang|dai truc trang|truc trang|tuyen tien liet|da day|tuyen giap|"
    r"buong trung|thuc quan|tuy|vom hong|mau|xuong|da|ruot))?"
)
# Khẳng định chẩn đoán (trên văn bản đã bỏ dấu, giữ nguyên độ dài để trả lại cụm gốc).
_DIAGNOSIS_PATTERNS = [
    r"\bban (da |dang |co the |co the da |co le |nhieu kha nang |rat co the |hau nhu |chac chan )?(bi|mac)\b",
    r"\bbenh nhan (da |dang |co the |co the da |co le |nhieu kha nang |rat co the )?(bi|mac) ung thu\b",
    r"\bchan doan (la|ban|xac dinh)\b",
    r"\bket luan (ban|la)\b.*ung thu",
    r"\b(chac chan|kha nang cao|nhieu kha nang|rat co the|co le|hau nhu chac chan) "
    r"(la |bi |da |dang )?(bi |mac )?ung thu\b",
    r"\b(day|no|khoi u nay|khoi nay|cuc nay|trieu chung nay|tinh trang nay|ket qua nay) (rat )?"
    r"(co the |chac chan |co le |nhieu kha nang |hau nhu )?(la|do) (dau hieu cua |bieu hien cua )?ung thu\b",
    r"\byou (have|are diagnosed)\b",
]
_RE = re.compile("|".join(_DIAGNOSIS_PATTERNS))
# Lời khuyên điều trị (Navigator, Copilot, hỏi đáp bệnh nhân đều không được tư vấn điều trị — S1).
_TREATMENT_PATTERNS = [
    r"\b(nen|can|phai|hay|khuyen|de nghi|co the) (\w+ ){0,2}(phau thuat|mo cat|mo lay|mo bo|cat bo|hoa tri|xa tri|"
    r"dung thuoc|uong thuoc|tiem thuoc|dieu tri bang|ghep)\b",
    r"\b(hoa tri|xa tri|lieu phap (nham trung|mien dich|hormone|hoc mon)|phac do( dieu tri)?)\b",
    r"\b(uong|dung) (thuoc )?(tamoxifen|letrozole|sorafenib|lenvatinib|entecavir|tenofovir|thuoc nam|thuoc bac)\b",
]
_TREATMENT = re.compile("|".join(_TREATMENT_PATTERNS))

_OUT_OF_SCOPE = re.compile(
    "|".join(
        [
            # "tôi có bị ung thư vú không?" — nhưng "có nguy cơ mắc ung thư phổi không?" là câu hỏi nguy cơ, hợp lệ.
            rf"(?<!nguy )(?<!nguy co )(?<!kha nang )(?<!phong )(?<!de )(co (bi|mac)|bi|mac) (benh )?ung thu"
            rf"{_CANCER_SITE} (khong|ko|chua|k)\b(?! (biet|ro|hieu|nen|can|co|duoc))",
            r"co phai (la )?ung thu",
            r"chan doan (giup|cho|xem)",
            r"(doc|xem|giai thich) (giup |ho )?(ket qua|phim|chi so)",
            r"ket qua .{0,25}(xet nghiem|sinh thiet|nhu anh|chup|ct|sieu am|noi soi|pap|hpv|psa|afp|cea)"
            r".{0,30}(co sao|nghia la|the nao|binh thuong|bat thuong|ung thu|xau)",
            r"ket qua (\w+ ){0,3}(xet nghiem|sinh thiet|giai phau benh|mo benh hoc|nhu anh|chup|ct|mri|sieu am|noi soi|"
            r"pap|hpv|psa|afp|cea|x ?quang)( \w+){0,3} (cua (toi|minh|em|tui)|ghi|bao|cho thay)\b",
            r"ket qua cua (toi|minh|em|tui) (ghi|bao|cho thay|la)\b",
            r"(chi so|psa|afp|cea|ca ?125|ca ?19.?9) .{0,25}(cao|thap|bat thuong|co sao|nghia la)",
            r"\b(psa|afp|cea|ca ?125|ca ?19 ?9|ca ?15 ?3)( cua (toi|minh|em|tui))?( la| bang| duoc)?\s?[:=]?\s?\d",
            r"\b(carcinoma|adenocarcinoma|sarcoma|bi-?rads|ti-?rads|cin ?[123]|asc-?us|asc-?h|lsil|hsil|ac tinh|"
            r"di can)\b",
            r"(cach|phuong phap|nen) dieu tri",
            r"dieu tri (the nao|ra sao|nhu the nao|o dau|bang gi)",
            r"\b(hoa tri|xa tri)\b",
            r"(co nen|nen|co can|can|co phai) (\w+ ){0,2}(phau thuat|mo|cat bo)\b"
            r"(?! (tai khoan|tk|ung dung|app|lich|rong|link|trang))",
            r"uong thuoc (gi|nao)",
        ]
    )
)
_INJECTION = re.compile(
    r"\bignore (all |the |your |any |previous |above |prior |earlier )*(instructions|rules|prompt|guidelines)|"
    r"disregard (all |the |your |any |previous |above |prior )*(system|instructions|rules|previous)|system prompt|"
    r"you are now|developer mode|jailbreak|"
    r"(bo qua|quen( di)?|phot lo|khong can tuan theo) (moi |tat ca |cac |nhung |toan bo )?"
    r"(huong dan|chi dan|quy tac|chi thi|rang buoc|nguyen tac|lenh)|"
    r"(quen|bo qua) (system|vai tro)|(tu (gio|bay gio|nay)|bay gio) (ban|may) (la|se la|hay|dong vai)\b|"
    r"dong vai (bac si|chuyen gia)|gia vo (ban )?(la|lam) (bac si|chuyen gia)"
)
_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
_LIST_MARKER = re.compile(r"^\s*\d+[.)]\s", re.MULTILINE)


class GuardrailViolation(Exception):
    pass


_NEGATED_CLAIM = re.compile(r"(khong co nghia la|khong phai la|khong phai|chua chac|khong|chua)\s*(la\s*)?$")
_CONDITIONAL = re.compile(r"\b(neu nhu|neu|khi|trong truong hop|truong hop|phong khi)\s*$")
_NEGATED_ADVICE = re.compile(r"\b(khong the|khong|chua|dung|khong nen|khong duoc|khong tu van)( \w+){0,4}\s*$")


def _aligned_fold(text: str) -> tuple[str, str]:
    """(văn bản gốc đã chuẩn hoá NFC/khoảng trắng, bản bỏ dấu CÙNG ĐỘ DÀI) — so khớp không dấu, trả lại cụm gốc."""
    clean = "".join(ch for ch in unicodedata.normalize("NFC", text) if unicodedata.category(ch) != "Cf")
    clean = _SPACES.sub(" ", clean)
    out: list[str] = []
    for ch in clean:
        base = fold(ch) if not ch.isspace() else " "
        out.append(base if len(base) == 1 else (ch.lower() if len(ch.lower()) == 1 else "?"))
    return clean, "".join(out)


def _hits(pattern: re.Pattern[str], text: str, skip_before: list[re.Pattern[str]], window: int = 30) -> list[str]:
    clean, folded = _aligned_fold(text)
    hits = []
    for m in pattern.finditer(folded):
        before = folded[max(0, m.start() - window) : m.start()]
        if not any(p.search(before) for p in skip_before):
            hits.append(clean[m.start() : m.end()])
    return hits


def find_diagnosis_language(text: str) -> list[str]:
    """Cụm từ khẳng định chẩn đoán (có dấu hoặc không dấu); bỏ qua câu phủ định ("không có nghĩa là bạn mắc bệnh")
    và câu điều kiện ("nếu bạn bị chảy máu bất thường, hãy đi khám")."""
    return _hits(_RE, text, [_NEGATED_CLAIM, _CONDITIONAL])


def find_treatment_advice(text: str) -> list[str]:
    """Cụm từ tư vấn điều trị ("bạn nên phẫu thuật", "hoá trị"…);
    bỏ qua câu từ chối ("mình không thể tư vấn hoá trị")."""
    return _hits(_TREATMENT, text, [_NEGATED_ADVICE])


def unsafe_output(text: str) -> str | None:
    """Lý do chặn một đoạn văn bản do LLM sinh ra trước khi tới người dùng/bác sĩ; None nếu không vi phạm."""
    if find_diagnosis_language(text):
        return "diagnosis_language"
    if find_treatment_advice(text):
        return "treatment_advice"
    if is_out_of_scope_request(text):
        return "out_of_scope"
    return None


def is_out_of_scope_request(text: str) -> bool:
    """Câu hỏi đòi chẩn đoán, đọc kết quả xét nghiệm/hình ảnh hoặc tư vấn điều trị."""
    return bool(_OUT_OF_SCOPE.search(fold(text)))


def looks_like_prompt_injection(text: str) -> bool:
    return bool(_INJECTION.search(fold(text)))


_DIGIT_WORDS = {"mot": 1, "hai": 2, "ba": 3, "bon": 4, "nam": 5, "lam": 5, "bay": 7, "tam": 8, "chin": 9}
# Số viết bằng chữ đi kèm đơn vị ("mỗi ba tháng", "bốn mươi tuổi"). "sáu"/"tư" chỉ tính trong số ghép với "mươi"
# vì trùng dạng với "sau"/"từ" ("sau lần khám", "từ tháng 3").
_SPELLED = re.compile(
    r"\b((?:(?:mot|hai|ba|bon|nam|lam|bay|tam|chin|muoi) )+(?:(?:sau|tu|mot|lam) )?)"
    r"(thang|nam|tuoi|lan|tuan|ngay|goi)\b"
)


def _spelled_numbers(text: str) -> list[str]:
    out: list[str] = []
    for m in _SPELLED.finditer(fold(text)):
        words = m.group(1).split()
        tens, units, seen_muoi = 0, 0, False
        for w in words:
            if w == "muoi":
                tens, units, seen_muoi = (units or 1) * 10, 0, True
            elif w in {"sau", "tu"} and not seen_muoi:
                break  # "sau"/"từ" không phải số khi đứng riêng
            else:
                units = {"sau": 6, "tu": 4}.get(w, _DIGIT_WORDS.get(w, 0))
        else:
            value = tens + units
            if value > 1:  # "một lần/một năm" là cách nói thông thường, không phải mốc số cần đối chiếu
                out.append(str(value))
    return out


def ungrounded_numbers(text: str, evidence: list[str]) -> list[str]:
    """Các con số trong `text` (kể cả số viết bằng chữ: "mỗi ba tháng") không xuất hiện ở bất kỳ bằng chứng nào
    (nguồn, gợi ý, lời người dùng)."""
    allowed = {n.replace(",", ".") for chunk in evidence for n in [*_NUMBER.findall(chunk), *_spelled_numbers(chunk)]}
    cleaned = _LIST_MARKER.sub("", text)
    numbers = [*_NUMBER.findall(cleaned), *_spelled_numbers(cleaned)]
    return [n for n in numbers if n.replace(",", ".") not in allowed]


def validate_plan(plan: ScreeningPlan) -> ScreeningPlan:
    """Raise GuardrailViolation nếu vi phạm; trả lại plan nếu ổn.

    Quét MỌI trường văn bản tự do của từng PlanItem (method, rationale, …) và general_advice; mỗi nguồn phải là
    tài liệu có trong kho guideline (cùng bộ doc_id mà bộ luật/RAG trích dẫn) — chặn kế hoạch sửa tay bịa nguồn.
    """
    from ai_core.rag.corpus import load_docs  # import muộn: chỉ đọc kho guideline khi thật sự kiểm tra plan

    known_docs = load_docs()
    problems: list[str] = []
    for i, item in enumerate(plan.items):
        if not item.sources:
            problems.append(f"item[{i}] không có nguồn")
        for name in type(item).model_fields:
            value = getattr(item, name)
            if type(value) is not str:  # bỏ qua enum (CancerType là str-Enum), số, ngày, danh sách nguồn
                continue
            for hit in find_diagnosis_language(value):
                problems.append(f"item[{i}].{name} chứa ngôn ngữ chẩn đoán: {hit!r}")
        for source in item.sources:
            if source.doc_id not in known_docs:
                problems.append(f"item[{i}] trích dẫn nguồn không có trong kho guideline: {source.doc_id!r}")
    for hit in find_diagnosis_language(plan.general_advice):
        problems.append(f"general_advice chứa ngôn ngữ chẩn đoán: {hit!r}")
    if problems:
        raise GuardrailViolation("; ".join(problems))
    return plan
