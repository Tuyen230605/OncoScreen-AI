#!/usr/bin/env python3
"""AGENT 1: NCI PDQ® & Hugging Face Guideline Crawler (RAG Corpus / Navigator).

Tuân thủ nghiêm ngặt Master Prompt & ràng buộc OncoScreen-AI:
- KHÔNG chẩn đoán, KHÔNG kê đơn/điều trị, KHÔNG đọc hình ảnh.
- Thu thập, lọc, chuẩn hóa thành Markdown + YAML Frontmatter 6 trường.
- Lưu trữ vào vinh-data/guidelines/ theo yêu cầu người dùng.
"""

from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Literal

from bs4 import BeautifulSoup
from pydantic import BaseModel, field_validator
import requests
import yaml

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Định vị thư mục lưu trữ theo yêu cầu người dùng
OUT_DIR = Path("vinh-data/guidelines")
MANIFEST = OUT_DIR / "_manifest.jsonl"
LOCAL_RAW_QA = Path("vinh-data/raw_data/_master_hf_datasets/CancerGov_QA.parquet")

UA = {"User-Agent": "OncoScreen-AI-research-crawler/1.0 (contact: vinh@oncoscreen.ai)"}
PDQ_INDEX = "https://www.cancer.gov/publications/pdq/information-summaries/screening"
SAFE_EPFL = {"cdc", "who", "cco", "nice", "wikidoc", "spor", "cma"}
QA_ALLOWED_TYPES = {"prevention", "symptoms", "susceptibility"}
QA_SCREEN_ONLY = {"exams and tests"}

CANCER_LABEL_VI = {
    "breast": "ung thư vú",
    "cervical": "ung thư cổ tử cung",
    "colorectal": "ung thư đại trực tràng",
    "lung": "ung thư phổi",
    "liver": "ung thư gan",
    "prostate": "ung thư tuyến tiền liệt",
    "other": "ung thư",
}

CANCER_KW = {
    "breast": r"\bbreast\b|mammogra",
    "cervical": r"\bcervi(x|cal)\b|\bhpv\b|pap (test|smear)",
    "colorectal": r"colorectal|\bcolon\b|\brectal\b|colonoscop|fecal occult",
    "lung": r"\blung\b|low-dose (ct|computed)",
    "liver": r"\bliver\b|hepatocellular|hepatitis [bc]",
    "prostate": r"prostate|\bpsa\b",
}

HARD = re.compile(
    r"childhood|pediatric|children|stage\s+(ii|iii|iv|2|3|4)\b|metasta|recurren|relapse|"
    r"palliative|hospice|chemo|treatment of|clinical trial",
    re.I,
)
SOFT = re.compile(
    r"surg|radiation|radiotherap|hormone therapy|immunotherap|targeted therapy|therapy",
    re.I,
)
KEEP = re.compile(
    r"risk|screen|prevent|symptom|sign|prepar|harm|benefit|who should|how often",
    re.I,
)
SCREEN_RE = re.compile(r"screen|early detection|prevent|risk factor|symptom", re.I)

# Bảng dịch chuẩn y khoa theo Mục 4 của Master Prompt
TERM_MAP = [
    (r"\bmammograms?\b", "chụp nhũ ảnh (X-quang tuyến vú)"),
    (r"\bPap tests?\b|\bPap smears?\b", "xét nghiệm Pap (phết tế bào cổ tử cung)"),
    (r"\bHPV tests?\b", "xét nghiệm HPV"),
    (r"\bcolonoscop(y|ies)\b", "nội soi đại trực tràng"),
    (r"\bFIT\b|\bfecal immunochemical tests?\b", "xét nghiệm miễn dịch tìm máu ẩn trong phân (FIT)"),
    (r"\bLDCT\b|\blow-dose computed tomography\b|\blow-dose CT\b", "chụp CT liều thấp (LDCT)"),
    (r"\bPSA tests?\b|\bPSA\b", "xét nghiệm PSA (kháng nguyên đặc hiệu tuyến tiền liệt)"),
    (r"\bultrasounds?\b", "siêu âm (ultrasound)"),
    (r"\bAFP\b|\balpha-fetoprotein\b", "xét nghiệm AFP (alpha-fetoprotein)"),
]


class FrontMatter(BaseModel):
    cancer_type: Literal["breast", "cervical", "colorectal", "lung", "liver", "prostate", "other"]
    source: str
    url: str
    gender: Literal["any", "female", "male"]
    risk_level: Literal["average", "high"]
    language: Literal["vi"] = "vi"

    @field_validator("source", "url")
    @classmethod
    def _nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("empty")
        return v.strip()


def detect_cancer(text: str) -> str | None:
    hits = {k: len(re.findall(p, text, re.I)) for k, p in CANCER_KW.items()}
    k, n = max(hits.items(), key=lambda kv: kv[1])
    return k if n >= 2 else None


def infer_gender(c: str) -> Literal["any", "female", "male"]:
    return {"cervical": "female", "breast": "female", "prostate": "male"}.get(c, "any")  # type: ignore


def infer_risk(text: str) -> Literal["average", "high"]:
    return (
        "high"
        if re.search(r"BRCA|family history|cirrhosis|hepatitis [bc]|heavy smok|pack-year|Lynch", text, re.I)
        else "average"
    )


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def keep_section(heading: str, body: str) -> bool:
    if HARD.search(heading):
        return False
    if SOFT.search(heading) and not KEEP.search(heading):
        return False
    return len(body.split()) >= 30


def apply_glossary(text: str) -> str:
    """Áp dụng bảng thuật ngữ bắt buộc của Mục 4."""
    for pattern, repl in TERM_MAP:
        text = re.sub(pattern, repl, text, flags=re.I)
    return text


def translate_header_vi(h: str, cancer: str) -> str:
    """Dịch tiêu đề section sang tiếng Việt tự chứa nghĩa (nêu rõ loại ung thư và đối tượng)."""
    c_label = CANCER_LABEL_VI.get(cancer, "ung thư")
    h_clean = h.strip()
    low = h_clean.lower()

    if "who is at risk" in low or "risk factor" in low:
        return f"Các yếu tố nguy cơ của {c_label}"
    if "how to prevent" in low or "prevention" in low:
        return f"Phòng ngừa và giảm thiểu nguy cơ {c_label}"
    if "symptom" in low or "sign" in low:
        return f"Dấu hiệu và triệu chứng cảnh báo sớm của {c_label}"
    if "who should be screened" in low:
        return f"Đối tượng và độ tuổi nên tầm soát {c_label}"
    if "screening test" in low or "tests used" in low:
        return f"Các phương pháp xét nghiệm tầm soát {c_label}"
    if "benefits and harms" in low:
        return f"Lợi ích và nguy cơ tiềm ẩn khi tầm soát {c_label}"
    if "patient preparation" in low:
        return f"Chuẩn bị của người bệnh trước khi khám và xét nghiệm {c_label}"
    if "screening frequency" in low or "how often" in low:
        return f"Tần suất và khoảng cách giữa các lần tầm soát {c_label}"
    if "general information" in low or "overview" in low:
        return f"Tổng quan về tầm soát và phát hiện sớm {c_label}"
    if "screening" in low:
        return f"Khuyến nghị tầm soát {c_label}"

    # Thay thế cơ bản
    h_out = h_clean
    h_out = re.sub(r"(?i)\bscreening\b", f"Tầm soát {c_label}", h_out)
    h_out = re.sub(r"(?i)\brisk factors?\b", f"Yếu tố nguy cơ {c_label}", h_out)
    h_out = re.sub(r"(?i)\bprevention\b", f"Phòng ngừa {c_label}", h_out)
    h_out = re.sub(r"(?i)\bsymptoms?\b", f"Triệu chứng {c_label}", h_out)
    return h_out


def clean_body_text(text: str) -> str:
    """Làm sạch văn bản, chuẩn hóa khoảng trắng và áp dụng thuật ngữ."""
    # Bỏ khoảng trắng thừa do trích xuất HTML
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return apply_glossary(text.strip())


def translate_source_label(raw_title: str, cancer: str, org: str, doc_type: str = "") -> str:
    """Tạo nhãn nguồn chuẩn '<Tổ chức> — <Tên tài liệu tiếng Việt>'."""
    c_label = CANCER_LABEL_VI.get(cancer, "ung thư").title()
    if "qa" in doc_type.lower():
        return f"{org} — Câu hỏi và giải đáp tầm soát {c_label}"
    if "patient" in doc_type.lower():
        return f"{org} — Tầm soát {c_label} (Bản dành cho bệnh nhân)"
    if "professional" in doc_type.lower() or "hp" in doc_type.lower():
        return f"{org} — Tầm soát {c_label} (Bản hướng dẫn chuyên môn)"
    return f"{org} — Hướng dẫn tầm soát và phòng ngừa {c_label}"


def write_doc(
    sections: list[tuple[str, str]],
    cancer: str,
    src_tag: str,
    title: str,
    url: str,
    org: str,
    doc_type: str,
    dry: bool = False,
    translate: bool = True,
) -> str:
    valid_sections = [(h, b) for h, b in sections if keep_section(h, b)]
    if len(valid_sections) < 2:
        return "too_few_sections"

    whole = " ".join(b for _, b in valid_sections)
    source_label = translate_source_label(title, cancer, org, doc_type)

    fm = FrontMatter(
        cancer_type=cancer,  # type: ignore
        source=source_label,
        url=url,
        gender=infer_gender(cancer),
        risk_level=infer_risk(whole),
        language="vi",
    )

    body_parts = []
    for h, b in valid_sections:
        h_tr = translate_header_vi(h, cancer) if translate else h
        b_clean = clean_body_text(b)
        body_parts.append(f"## {h_tr}\n{b_clean}")

    body = "\n\n".join(body_parts)
    path = OUT_DIR / f"{cancer}-{src_tag}-{slug(title)}.md"

    if dry:
        return "ok(dry)"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    header_yaml = yaml.safe_dump(fm.model_dump(), allow_unicode=True, sort_keys=False)
    content = f"---\n{header_yaml}---\n{body}\n"
    path.write_text(content, encoding="utf-8")

    with MANIFEST.open("a", encoding="utf-8") as f:
        meta = {
            "file": path.name,
            "url": url,
            "origin": src_tag,
            "cancer_type": cancer,
            "source": source_label,
            "sections_count": len(valid_sections),
            "retrieved": dt.date.today().isoformat(),
        }
        f.write(json.dumps(meta, ensure_ascii=False) + "\n")
    return "ok"


# ==============================================================================
# Nguồn 3: cancer.gov PDQ (HTML Crawler)
# ==============================================================================
def parse_sections(html: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    root = soup.find("main") or soup.find("article") or soup
    secs, cur_h, buf = [], None, []
    for el in root.find_all(["h2", "h3", "h4", "p", "ul", "ol"]):
        if el.name == "p" and el.find_parent(["ul", "ol", "table"]):
            continue
        if el.name == "h2":
            if cur_h and buf:
                secs.append((cur_h, "\n".join(buf)))
            cur_h, buf = el.get_text(" ", strip=True), []
        elif cur_h is None:
            continue
        elif el.name in ("h3", "h4"):
            buf.append("#" * (3 if el.name == "h3" else 4) + " " + el.get_text(" ", strip=True))
        elif el.name == "p":
            buf.append(el.get_text(" ", strip=True))
        else:
            buf += ["- " + li.get_text(" ", strip=True) for li in el.find_all("li", recursive=False)]
    if cur_h and buf:
        secs.append((cur_h, "\n".join(buf)))
    return secs


def crawl_pdq(limit: int, dry: bool, translate: bool) -> dict[str, int]:
    print("\n--- Crawling NCI PDQ Screening (HTML) ---", flush=True)
    s = requests.Session()
    s.headers.update(UA)
    try:
        resp = s.get(PDQ_INDEX, timeout=30)
        idx = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"[!] Lỗi kết nối trang index PDQ: {e}", flush=True)
        return {"error_index": 1}

    links = set()
    for a in idx.find_all("a", href=True):
        href = a["href"]
        if "screening-pdq" in href:
            full = "https://www.cancer.gov" + href if href.startswith("/") else href
            links.add(full)

    # Ưu tiên bản Patient (/patient/) trước bản Health Professional (/hp/)
    sorted_links = sorted(list(links), key=lambda u: ("/hp/" in u, u))[:limit]
    print(f" -> Khám phá được {len(sorted_links)} link PDQ (đã giới hạn {limit})", flush=True)

    stats: Counter = Counter()
    for u in sorted_links:
        time.sleep(1.5)  # Tuân thủ robots.txt và delay >= 1.5s
        try:
            html = s.get(u, timeout=30).text
            soup = BeautifulSoup(html, "html.parser")
            h1 = soup.find("h1")
            title = h1.get_text(" ", strip=True) if h1 else u.split("/")[-1]
            secs = parse_sections(html)

            comb = title + " " + " ".join(h for h, _ in secs) + " " + (secs[0][1] if secs else "")
            cancer = detect_cancer(comb)

            if cancer is None or cancer == "other":
                stats["not_target_cancer"] += 1
                continue

            doc_type = "patient" if "/patient/" in u else "professional"
            res = write_doc(
                sections=secs,
                cancer=cancer,
                src_tag="nci-pdq",
                title=title,
                url=u,
                org="NCI PDQ",
                doc_type=doc_type,
                dry=dry,
                translate=translate,
            )
            stats[res] += 1
        except Exception as e:
            stats[f"error_{type(e).__name__}"] += 1

    print("PDQ result:", dict(stats), flush=True)
    return dict(stats)


# ==============================================================================
# Nguồn 1: CancerGov_QA (Hugging Face)
# ==============================================================================
def crawl_qa(limit: int, dry: bool, translate: bool) -> dict[str, int]:
    print("\n--- Crawling Pedrampedram/CancerGov_QA ---", flush=True)
    records = []
    # Ưu tiên nạp từ cache local parquet nếu có
    if LOCAL_RAW_QA.exists():
        import pyarrow.parquet as pq

        table = pq.read_table(str(LOCAL_RAW_QA))
        records = table.to_pylist()
        print(f" -> Đã nạp {len(records)} dòng từ local cache {LOCAL_RAW_QA}", flush=True)
    else:
        from datasets import load_dataset

        ds = load_dataset("Pedrampedram/CancerGov_QA", split="train")
        records = list(ds)

    qtype_counter = Counter(r["question_type"] for r in records)
    print("question_type Counter (toàn bộ dataset):", flush=True)
    for qt, count in qtype_counter.most_common():
        print(f"   - {qt}: {count}", flush=True)

    groups: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for r in records:
        qt = str(r["question_type"]).lower()
        q_text = str(r["question_text"])
        a_text = str(r["answer_text"])
        ok = qt in QA_ALLOWED_TYPES or (qt in QA_SCREEN_ONLY and SCREEN_RE.search(q_text))
        if ok:
            key = (str(r["document_id"]), str(r["focus"]))
            groups.setdefault(key, []).append((q_text, a_text))

    print(f" -> Tổng số nhóm tài liệu sau lọc câu hỏi hợp lệ: {len(groups)}", flush=True)
    stats: Counter = Counter()

    for (doc, focus), qas in list(groups.items())[:limit]:
        comb = focus + " " + " ".join(q + " " + a for q, a in qas)
        cancer = detect_cancer(comb)
        if cancer is None or cancer == "other":
            stats["not_target_cancer"] += 1
            continue

        url = f"https://www.cancer.gov/ (document_id={doc})"
        res = write_doc(
            sections=qas,
            cancer=cancer,
            src_tag="nci-qa",
            title=focus or doc,
            url=url,
            org="NCI PDQ",
            doc_type="qa",
            dry=dry,
            translate=translate,
        )
        stats[res] += 1

    print("QA result:", dict(stats), flush=True)
    return dict(stats)


# ==============================================================================
# Nguồn 2: epfl-llm/guidelines (Streaming)
# ==============================================================================
def crawl_epfl(limit: int, dry: bool, translate: bool) -> dict[str, int]:
    print("\n--- Crawling epfl-llm/guidelines (streaming=True) ---", flush=True)
    stats: Counter = Counter()
    try:
        from datasets import load_dataset

        ds = load_dataset("epfl-llm/guidelines", split="train", streaming=True)
        print("columns:", ds.column_names, flush=True)

        n = 0
        for r in ds:
            source_tag = str(r.get("source", "")).lower()
            if source_tag not in SAFE_EPFL:
                continue

            title = str(r.get("title") or "")
            if not SCREEN_RE.search(title):
                continue

            overview = str(r.get("overview") or "")
            cancer = detect_cancer(title + " " + overview)
            if cancer is None or cancer == "other":
                continue

            clean_text = str(r.get("clean_text") or "")
            parts = re.split(r"(?m)^#{1,3}\s+(.+)$", clean_text)
            secs = [(parts[i].strip(), parts[i + 1].strip()) for i in range(1, len(parts) - 1, 2)]

            if not secs:
                stats["no_headings_skip"] += 1
                continue

            url = str(r.get("url") or f"https://guidelines.epfl.ch/{r.get('id')}")
            res = write_doc(
                sections=secs,
                cancer=cancer,
                src_tag=source_tag,
                title=title,
                url=url,
                org=source_tag.upper(),
                doc_type="guideline",
                dry=dry,
                translate=translate,
            )
            stats[res] += 1
            n += 1
            if n >= limit:
                break
    except Exception as e:
        print(f"[!] epfl stream error: {e}", flush=True)
        stats["epfl_stream_error"] += 1

    print("EPFL result:", dict(stats), flush=True)
    return dict(stats)


# ==============================================================================
# Xác thực chất lượng Corpus (Validation)
# ==============================================================================
def validate_corpus() -> None:
    print("\n=== KIỂM THỬ CHẤT LƯỢNG CORPUS (validate_corpus) ===", flush=True)
    files = list(OUT_DIR.glob("*.md"))
    print(f"Tổng số tệp Markdown trong {OUT_DIR}: {len(files)}", flush=True)

    bad = []
    cancer_stats: Counter = Counter()

    for p in files:
        text = p.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
        if not m:
            bad.append((p.name, "Thiếu hoặc sai cú pháp YAML Frontmatter"))
            continue

        try:
            fm_data = yaml.safe_load(m.group(1))
            fm = FrontMatter(**fm_data)
            cancer_stats[fm.cancer_type] += 1

            heads = re.findall(r"(?m)^## (.+)$", m.group(2))
            if not heads:
                bad.append((p.name, "Không tìm thấy tiêu đề ## nào"))
            if len(heads) < 2:
                bad.append((p.name, f"Quá ít section: {len(heads)} < 2"))

            for h in heads:
                if HARD.search(h):
                    bad.append((p.name, f"Vi phạm EXCLUDE HARD trong tiêu đề: '{h}'"))
        except Exception as e:
            bad.append((p.name, repr(e)))

    print("Phân bố theo cancer_type:", flush=True)
    for ct, count in cancer_stats.most_common():
        print(f"   - {ct}: {count} files", flush=True)

    print(f"Số tệp lỗi: {len(bad)}", flush=True)
    if bad:
        for fname, err in bad[:10]:
            print(f"   [!] {fname}: {err}", flush=True)
    else:
        print("[V] TOÀN BỘ CORPUS HỢP LỆ VÀ ĐẠT 100% TIÊU CHUẨN!", flush=True)


# ==============================================================================
# Entry point
# ==============================================================================
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["pdq", "qa", "epfl", "all"], default="all")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-translate", action="store_true")
    args = ap.parse_args()

    tr = not args.no_translate
    print("==================================================================", flush=True)
    print(
        f" KHỞI CHẠY AGENT 1 CRAWLER (source={args.source}, limit={args.limit}, dry_run={args.dry_run}, translate={tr})",
        flush=True,
    )
    print("==================================================================", flush=True)

    if args.source in ("qa", "all"):
        crawl_qa(args.limit, args.dry_run, tr)
    if args.source in ("pdq", "all"):
        crawl_pdq(args.limit, args.dry_run, tr)
    if args.source in ("epfl", "all"):
        crawl_epfl(args.limit, args.dry_run, tr)

    if not args.dry_run:
        validate_corpus()
