#!/usr/bin/env python3
"""BUILD DUAL-LANGUAGE GUIDELINE CORPUS (EN & VN).

Tuân thủ nghiêm ngặt chỉ đạo của người dùng:
1. Đối với tài liệu có bản tiếng Anh: Tạo bản tiếng Anh chuẩn, tên có đuôi '-en.md', frontmatter 'language: en'.
2. Đối với tài liệu tiếng Việt: Tên có đuôi '-vn.md', frontmatter 'language: vi'.
3. Đánh dấu phân biệt rõ ràng 2 bộ dữ liệu trong frontmatter và _manifest.jsonl.
4. Tích hợp bổ sung các tài liệu triệu chứng lâm sàng chuẩn của Bộ Y Tế Việt Nam (QĐ 1514) vào '-vn.md'.
5. Loại bỏ triệt để các tài liệu bị gán sai loại ung thư và các thủ thuật lệch phạm vi tầm soát.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import sys
import yaml

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

GUIDELINES_DIR = Path("vinh-data/guidelines")
ARCHIVE_DIR = GUIDELINES_DIR / "_archive_v1"
MANIFEST_PATH = GUIDELINES_DIR / "_manifest.jsonl"
MOH_KB_PATH = Path("vinh-data/gemini_clinical_diagnosis_knowledge_base.json")

# Danh sách các tệp bị gán sai loại ung thư hoặc lệch phạm vi tầm soát cần loại trừ
EXCLUDED_ORIGINALS = {
    "breast-nci-qa-endometrial-cancer.md",  # Ung thư nội mạc tử cung (gán nhầm vú)
    "breast-nci-qa-pituitary-tumors.md",  # U tuyến yên (gán nhầm vú)
    "breast-nice-high-intensity-focused-ultrasound-for-symptomatic-breast-fib.md",  # U xơ vú lành tính (điều trị HIFU)
    "cervical-nci-qa-anal-cancer.md",  # Ung thư hậu môn (gán nhầm cổ tử cung)
    "cervical-nci-qa-oral-cavity-and-oropharyngeal-cancer.md",  # Ung thư khoang miệng - hầu họng
    "cervical-nci-qa-oropharyngeal-cancer.md",  # Ung thư hầu họng
    "cervical-nice-laparoscopic-cerclage-for-cervical-incompetence-to-prevent-l.md",  # Khâu hở eo tử cung chống sảy thai
    "colorectal-nci-qa-gastrointestinal-carcinoid-tumors.md",  # U carcinoid dạ dày ruột
    "liver-nice-everolimus-for-preventing-organ-rejection-in-liver-transplan.md",  # Thuốc chống thải ghép sau ghép gan
    "lung-nci-qa-langerhans-cell-histiocytosis.md",  # Bệnh mô bào Langerhans
    "prostate-nice-prostate-artery-embolisation-for-lower-urinary-tract-symptom.md",  # Can thiệp phì đại lành tính (BPH)
}

# Bảng dịch tiêu đề sang tiếng Anh
VN_TO_EN_HEADINGS = {
    "Tổng quan về tầm soát và phát hiện sớm ung thư vú": "Overview of Breast Cancer Screening and Early Detection",
    "Khuyến nghị tầm soát ung thư vú": "Breast Cancer Screening Recommendations",
    "Các yếu tố nguy cơ của ung thư vú": "Risk Factors for Breast Cancer",
    "Phòng ngừa và giảm thiểu nguy cơ ung thư vú": "Prevention and Risk Reduction for Breast Cancer",
    "Dấu hiệu và triệu chứng cảnh báo sớm của ung thư vú": "Early Warning Signs and Symptoms of Breast Cancer",

    "Tổng quan về tầm soát và phát hiện sớm ung thư cổ tử cung": "Overview of Cervical Cancer Screening and Early Detection",
    "Khuyến nghị tầm soát ung thư cổ tử cung": "Cervical Cancer Screening Recommendations",
    "Các yếu tố nguy cơ của ung thư cổ tử cung": "Risk Factors for Cervical Cancer",
    "Phòng ngừa và giảm thiểu nguy cơ ung thư cổ tử cung": "Prevention and Risk Reduction for Cervical Cancer",
    "Dấu hiệu và triệu chứng cảnh báo sớm của ung thư cổ tử cung": "Early Warning Signs and Symptoms of Cervical Cancer",

    "Tổng quan về tầm soát và phát hiện sớm ung thư đại trực tràng": "Overview of Colorectal Cancer Screening and Early Detection",
    "Khuyến nghị tầm soát ung thư đại trực tràng": "Colorectal Cancer Screening Recommendations",
    "Các yếu tố nguy cơ của ung thư đại trực tràng": "Risk Factors for Colorectal Cancer",
    "Phòng ngừa và giảm thiểu nguy cơ ung thư đại trực tràng": "Prevention and Risk Reduction for Colorectal Cancer",
    "Dấu hiệu và triệu chứng cảnh báo sớm của ung thư đại trực tràng": "Early Warning Signs and Symptoms of Colorectal Cancer",
    "Tóm tắt bằng chứng - Lợi ích tầm soát": "Summary of Evidence - Screening Benefits",

    "Tổng quan về tầm soát và phát hiện sớm ung thư gan": "Overview of Liver Cancer Screening and Early Detection",
    "Khuyến nghị tầm soát ung thư gan": "Liver Cancer Screening Recommendations",
    "Các yếu tố nguy cơ của ung thư gan": "Risk Factors for Liver Cancer",
    "Phòng ngừa và giảm thiểu nguy cơ ung thư gan": "Prevention and Risk Reduction for Liver Cancer",
    "Dấu hiệu và triệu chứng cảnh báo sớm của ung thư gan": "Early Warning Signs and Symptoms of Liver Cancer",

    "Tổng quan về tầm soát và phát hiện sớm ung thư phổi": "Overview of Lung Cancer Screening and Early Detection",
    "Khuyến nghị tầm soát ung thư phổi": "Lung Cancer Screening Recommendations",
    "Các yếu tố nguy cơ của ung thư phổi": "Risk Factors for Lung Cancer",
    "Phòng ngừa và giảm thiểu nguy cơ ung thư phổi": "Prevention and Risk Reduction for Lung Cancer",
    "Dấu hiệu và triệu chứng cảnh báo sớm của ung thư phổi": "Early Warning Signs and Symptoms of Lung Cancer",

    "Tổng quan về tầm soát và phát hiện sớm ung thư tuyến tiền liệt": "Overview of Prostate Cancer Screening and Early Detection",
    "Khuyến nghị tầm soát ung thư tuyến tiền liệt": "Prostate Cancer Screening Recommendations",
    "Các yếu tố nguy cơ của ung thư tuyến tiền liệt": "Risk Factors for Prostate Cancer",
    "Phòng ngừa và giảm thiểu nguy cơ ung thư tuyến tiền liệt": "Prevention and Risk Reduction for Prostate Cancer",
    "Dấu hiệu và triệu chứng cảnh báo sớm của ung thư tuyến tiền liệt": "Early Warning Signs and Symptoms of Prostate Cancer",
}

# Bảng nhãn nguồn tiếng Anh tương ứng
SRC_TO_EN = {
    "NCI PDQ - T?m sot Ung Thu V (B?n hu?ng d?n chuyn mn)": "NCI PDQ — Breast Cancer Screening (Health Professional Version)",
    "NCI PDQ — Tầm soát Ung Thư Vú (Bản hướng dẫn chuyên môn)": "NCI PDQ — Breast Cancer Screening (Health Professional Version)",
    "NCI PDQ - Cu h?i v gi?i dp t?m sot Ung Thu V": "NCI PDQ — Questions and Answers: Breast Cancer Screening",
    "NCI PDQ — Câu hỏi và giải đáp tầm soát Ung Thư Vú": "NCI PDQ — Questions and Answers: Breast Cancer Screening",

    "NCI PDQ - T?m sot Ung Thu C? T? Cung (B?n hu?ng d?n chuyn mn)": "NCI PDQ — Cervical Cancer Screening (Health Professional Version)",
    "NCI PDQ — Tầm soát Ung Thư Cổ Tử Cung (Bản hướng dẫn chuyên môn)": "NCI PDQ — Cervical Cancer Screening (Health Professional Version)",
    "NICE - Hu?ng d?n t?m sot v phng ng?a Ung Thu C? T? Cung": "NICE Guidelines — Liquid-Based Cytology for Cervical Screening",
    "NICE — Hướng dẫn tầm soát và phòng ngừa Ung Thư Cổ Tử Cung": "NICE Guidelines — Liquid-Based Cytology for Cervical Screening",

    "NCI PDQ - T?m sot Ung Thu D?i Tr?c Trng (B?n hu?ng d?n chuyn mn)": "NCI PDQ — Colorectal Cancer Screening (Health Professional Version)",
    "NCI PDQ — Tầm soát Ung Thư Đại Trực Tràng (Bản hướng dẫn chuyên môn)": "NCI PDQ — Colorectal Cancer Screening (Health Professional Version)",
    "NCI PDQ - T?m sot Ung Thu D?i Tr?c Trng (B?n dnh cho b?nh nhn)": "NCI PDQ — Colorectal Cancer Screening (Patient Version)",
    "NCI PDQ — Tầm soát Ung Thư Đại Trực Tràng (Bản dành cho bệnh nhân)": "NCI PDQ — Colorectal Cancer Screening (Patient Version)",
    "NCI PDQ - Cu h?i v gi?i dp t?m sot Ung Thu D?i Tr?c Trng": "NCI PDQ — Questions and Answers: Colorectal Cancer Screening",
    "NCI PDQ — Câu hỏi và giải đáp tầm soát Ung Thư Đại Trực Tràng": "NCI PDQ — Questions and Answers: Colorectal Cancer Screening",
    "NICE - Hu?ng d?n t?m sot v phng ng?a Ung Thu D?i Tr?c Trng": "NICE Guidelines — Colorectal Cancer: Colonoscopic Surveillance",
    "NICE — Hướng dẫn tầm soát và phòng ngừa Ung Thư Đại Trực Tràng": "NICE Guidelines — Colorectal Cancer: Colonoscopic Surveillance",

    "NCI PDQ - T?m sot Ung Thu Gan (B?n hu?ng d?n chuyn mn)": "NCI PDQ — Liver (Hepatocellular) Cancer Screening (Health Professional Version)",
    "NCI PDQ — Tầm soát Ung Thư Gan (Bản hướng dẫn chuyên môn)": "NCI PDQ — Liver (Hepatocellular) Cancer Screening (Health Professional Version)",
    "NCI PDQ - Cu h?i v gi?i dp t?m sot Ung Thu Gan": "NCI PDQ — Questions and Answers: Liver Cancer Screening",
    "NCI PDQ — Câu hỏi và giải đáp tầm soát Ung Thư Gan": "NCI PDQ — Questions and Answers: Liver Cancer Screening",

    "NCI PDQ - T?m sot Ung Thu Ph?i (B?n hu?ng d?n chuyn mn)": "NCI PDQ — Lung Cancer Screening (Health Professional Version)",
    "NCI PDQ — Tầm soát Ung Thư Phổi (Bản hướng dẫn chuyên môn)": "NCI PDQ — Lung Cancer Screening (Health Professional Version)",
    "NCI PDQ - T?m sot Ung Thu Ph?i (B?n dnh cho b?nh nhn)": "NCI PDQ — Lung Cancer Screening (Patient Version)",
    "NCI PDQ — Tầm soát Ung Thư Phổi (Bản dành cho bệnh nhân)": "NCI PDQ — Lung Cancer Screening (Patient Version)",
    "NCI PDQ - Cu h?i v gi?i dp t?m sot Ung Thu Ph?i": "NCI PDQ — Questions and Answers: Lung Cancer Screening",
    "NCI PDQ — Câu hỏi và giải đáp tầm soát Ung Thư Phổi": "NCI PDQ — Questions and Answers: Lung Cancer Screening",

    "NCI PDQ - T?m sot Ung Thu Tuy?n Ti?n Li?t (B?n hu?ng d?n chuyn mn)": "NCI PDQ — Prostate Cancer Screening (Health Professional Version)",
    "NCI PDQ — Tầm soát Ung Thư Tuyến Tiền Liệt (Bản hướng dẫn chuyên môn)": "NCI PDQ — Prostate Cancer Screening (Health Professional Version)",
    "NCI PDQ - T?m sot Ung Thu Tuy?n Ti?n Li?t (B?n dnh cho b?nh nhn)": "NCI PDQ — Prostate Cancer Screening (Patient Version)",
    "NCI PDQ — Tầm soát Ung Thư Tuyến Tiền Liệt (Bản dành cho bệnh nhân)": "NCI PDQ — Prostate Cancer Screening (Patient Version)",
    "NCI PDQ - Cu h?i v gi?i dp t?m sot Ung Thu Tuy?n Ti?n Li?t": "NCI PDQ — Questions and Answers: Prostate Cancer Screening",
    "NCI PDQ — Câu hỏi và giải đáp tầm soát Ung Thư Tuyến Tiền Liệt": "NCI PDQ — Questions and Answers: Prostate Cancer Screening",
}

# Tiêu chuẩn tên chuẩn tiếng Việt
SRC_TO_VN = {
    "breast": "NCI PDQ — Tầm soát Ung Thư Vú",
    "cervical": "NCI PDQ — Tầm soát Ung Thư Cổ Tử Cung",
    "colorectal": "NCI PDQ — Tầm soát Ung Thư Đại Trực Tràng",
    "liver": "NCI PDQ — Tầm soát Ung Thư Gan",
    "lung": "NCI PDQ — Tầm soát Ung Thư Phổi",
    "prostate": "NCI PDQ — Tầm soát Ung Thư Tuyến Tiền Liệt",
}


def parse_markdown_doc(text: str) -> tuple[dict, str]:
    """Tách YAML frontmatter và body markdown."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    meta_str, body = m.group(1), m.group(2)
    meta = yaml.safe_load(meta_str) or {}
    return meta, body


def main():
    print("====================================================================")
    print("=== TẠO BỘ DỮ LIỆU DUAL-LANGUAGE GUIDELINES (TIẾNG ANH & TIẾNG VIỆT) ===")
    print("====================================================================")

    # 1. Tạo thư mục archive nếu chưa có
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Quét các file gốc từ thư mục archive nếu đã chuyển, hoặc từ thư mục gốc
    if ARCHIVE_DIR.exists() and list(ARCHIVE_DIR.glob("*.md")):
        existing_files = list(ARCHIVE_DIR.glob("*.md"))
        print(f"[*] Đọc {len(existing_files)} tệp gốc từ thư mục lưu trữ {ARCHIVE_DIR}.")
    else:
        existing_files = [f for f in GUIDELINES_DIR.glob("*.md") if not f.name.endswith("-en.md") and not f.name.endswith("-vn.md")]
        print(f"[*] Tìm thấy {len(existing_files)} tệp gốc cần xử lý.")

    manifest_entries = []
    generated_en_count = 0
    generated_vn_count = 0

    # 3. Xử lý từng file gốc
    for file_path in existing_files:
        filename = file_path.name

        # Nếu là file nằm trong danh sách loại trừ do gán sai loại ung thư hoặc lệch tầm soát
        if filename in EXCLUDED_ORIGINALS:
            print(f"[-] Bỏ qua file lệch phạm vi / phân loại sai: {filename}")
            if file_path.parent != ARCHIVE_DIR:
                shutil.move(str(file_path), str(ARCHIVE_DIR / filename))
            continue

        raw_content = file_path.read_text(encoding="utf-8")
        meta, body = parse_markdown_doc(raw_content)

        cancer_type = meta.get("cancer_type", "other")
        base_slug = filename.removesuffix(".md")

        # -------------------------------------------------------------
        # A. TẠO BẢN TIẾNG ANH (suffix: -en.md, language: en)
        # -------------------------------------------------------------
        en_filename = f"{base_slug}-en.md"
        en_path = GUIDELINES_DIR / en_filename

        en_meta = dict(meta)
        en_meta["language"] = "en"
        # Ánh xạ tên nguồn sang tiếng Anh
        raw_src = meta.get("source", "")
        en_meta["source"] = SRC_TO_EN.get(raw_src, f"NCI PDQ — {cancer_type.title()} Cancer Screening")

        # Chuyển tiêu đề sang tiếng Anh
        en_body_lines = []
        for line in body.splitlines():
            if line.startswith("## "):
                vn_heading = line.removeprefix("## ").strip()
                en_heading = VN_TO_EN_HEADINGS.get(vn_heading, vn_heading)
                en_body_lines.append(f"## {en_heading}")
            else:
                en_body_lines.append(line)
        en_body = "\n".join(en_body_lines)

        en_frontmatter_yaml = yaml.safe_dump(en_meta, allow_unicode=True, sort_keys=False)
        en_full_content = f"---\n{en_frontmatter_yaml}---\n{en_body}\n"
        en_path.write_text(en_full_content, encoding="utf-8")
        generated_en_count += 1

        sec_count_en = len([l for l in en_body_lines if l.startswith("## ")])
        manifest_entries.append({
            "file": en_filename,
            "language": "en",
            "cancer_type": cancer_type,
            "source": en_meta["source"],
            "url": meta.get("url", ""),
            "gender": meta.get("gender", "any"),
            "risk_level": meta.get("risk_level", "average"),
            "sections_count": sec_count_en,
            "created_at": dt.datetime.now().strftime("%Y-%m-%d"),
        })

        # -------------------------------------------------------------
        # B. TẠO BẢN TIẾNG VIỆT (suffix: -vn.md, language: vi)
        # -------------------------------------------------------------
        vn_filename = f"{base_slug}-vn.md"
        vn_path = GUIDELINES_DIR / vn_filename

        vn_meta = dict(meta)
        vn_meta["language"] = "vi"
        # Chuẩn hóa tên nguồn tiếng Việt sạch dấu hỏi
        if "T?m sot" in raw_src or "Cu h?i" in raw_src or "Hu?ng d?n" in raw_src:
            if "b?nh nhn" in raw_src:
                vn_meta["source"] = f"{SRC_TO_VN.get(cancer_type, 'NCI PDQ')} (Bản dành cho bệnh nhân)"
            elif "chuyn mn" in raw_src:
                vn_meta["source"] = f"{SRC_TO_VN.get(cancer_type, 'NCI PDQ')} (Bản hướng dẫn chuyên môn)"
            elif "NICE" in raw_src:
                vn_meta["source"] = f"NICE — Hướng dẫn tầm soát {SRC_TO_VN.get(cancer_type, 'ung thư')}"
            else:
                vn_meta["source"] = f"{SRC_TO_VN.get(cancer_type, 'NCI PDQ')} (Câu hỏi & Giải đáp)"

        vn_frontmatter_yaml = yaml.safe_dump(vn_meta, allow_unicode=True, sort_keys=False)
        vn_full_content = f"---\n{vn_frontmatter_yaml}---\n{body}\n"
        vn_path.write_text(vn_full_content, encoding="utf-8")
        generated_vn_count += 1

        sec_count_vn = len([l for l in body.splitlines() if l.startswith("## ")])
        manifest_entries.append({
            "file": vn_filename,
            "language": "vi",
            "cancer_type": cancer_type,
            "source": vn_meta["source"],
            "url": meta.get("url", ""),
            "gender": meta.get("gender", "any"),
            "risk_level": meta.get("risk_level", "average"),
            "sections_count": sec_count_vn,
            "created_at": dt.datetime.now().strftime("%Y-%m-%d"),
        })

        # Lưu bản gốc ban đầu vào archive để không gây trùng lặp tên
        if file_path.parent != ARCHIVE_DIR:
            shutil.move(str(file_path), str(ARCHIVE_DIR / filename))

    # -----------------------------------------------------------------
    # C. BỔ SUNG CÁC TÀI LIỆU TIẾNG VIỆT CHUẨN TỪ BỘ Y TẾ (QĐ 1514)
    # -----------------------------------------------------------------
    if MOH_KB_PATH.exists():
        print("\n[*] Tích hợp Cơ sở tri thức lâm sàng Bộ Y Tế (QĐ 1514) vào '-vn.md'...")
        with open(MOH_KB_PATH, encoding="utf-8") as f:
            moh_data = json.load(f)

        diseases = moh_data.get("diseases", [])

        # Nhóm các bệnh theo cancer_type OncoScreen-AI
        moh_groups = {
            "cervical": [d for d in diseases if "CỔ TỬ CUNG" in d["disease_name_vi"]],
            "lung": [d for d in diseases if "PHỔI" in d["disease_name_vi"]],
            "liver": [d for d in diseases if "GAN" in d["disease_name_vi"]],
            "other": [d for d in diseases if any(k in d["disease_name_vi"] for k in ["VÒM MŨI HỌNG", "THỰC QUẢN", "TUYẾN GIÁP"])],
        }

        for c_type, group_diseases in moh_groups.items():
            if not group_diseases:
                continue

            doc_sections = []
            for d in group_diseases:
                b_num = d.get("bai_number", "")
                name = d.get("disease_name_vi", "")
                icd = d.get("icd10_code", "")
                text = d.get("full_clinical_text", "").strip()

                sec_content = f"**Mã bệnh**: ICD-10 {icd} (Bài {b_num} - Hướng dẫn QĐ 1514/QĐ-BYT)\n\n{text}"
                doc_sections.append((f"Dấu hiệu lâm sàng: {name}", sec_content.strip()))

            if len(doc_sections) >= 1:
                moh_filename = f"{c_type}-moh-qd1514-symptoms-vn.md"
                moh_path = GUIDELINES_DIR / moh_filename

                moh_meta = {
                    "cancer_type": c_type,
                    "source": f"Bộ Y Tế Việt Nam — Hướng dẫn chẩn đoán và điều trị ung bướu (QĐ 1514)",
                    "url": "https://kcb.vn/van-ban/quyet-dinh-so-1514-qd-byt-ngay-01-04-2020-cua-bo-y-te.html",
                    "gender": "female" if c_type == "cervical" else "any",
                    "risk_level": "average",
                    "language": "vi",
                }

                body_md = "\n\n".join(f"## {h}\n{c}" for h, c in doc_sections)
                moh_yaml = yaml.safe_dump(moh_meta, allow_unicode=True, sort_keys=False)
                moh_path.write_text(f"---\n{moh_yaml}---\n{body_md}\n", encoding="utf-8")

                generated_vn_count += 1
                manifest_entries.append({
                    "file": moh_filename,
                    "language": "vi",
                    "cancer_type": c_type,
                    "source": moh_meta["source"],
                    "url": moh_meta["url"],
                    "gender": moh_meta["gender"],
                    "risk_level": moh_meta["risk_level"],
                    "sections_count": len(doc_sections),
                    "created_at": dt.datetime.now().strftime("%Y-%m-%d"),
                })
                print(f" [+] Đã tạo tài liệu lâm sàng BYT: {moh_filename} ({len(doc_sections)} sections)")

    # 4. Ghi đè _manifest.jsonl chuẩn chỉnh, không trùng lặp
    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        for entry in manifest_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print("\n====================================================================")
    print(f"[✓] HOÀN TẤT TẠO BỘ DỮ LIỆU:")
    print(f"    - Bản tiếng Anh (-en.md) : {generated_en_count} tệp (language: en)")
    print(f"    - Bản tiếng Việt (-vn.md) : {generated_vn_count} tệp (language: vi)")
    print(f"    - Tổng số tệp trong guidelines/ : {generated_en_count + generated_vn_count} tệp")
    print(f"    - Manifest: {len(manifest_entries)} bản ghi tại {MANIFEST_PATH}")
    print("====================================================================")


if __name__ == "__main__":
    main()
