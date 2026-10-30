#!/usr/bin/env python3
"""USPSTF GUIDELINES GENERATOR (DUAL LANGUAGE: EN & VN).

Trích xuất toàn bộ 8 tài liệu khuyến nghị USPSTF chính thức từ vinh-data/raw_data/
thành các tệp guideline Markdown chuẩn YAML Frontmatter (gồm cả -en.md và -vn.md)
theo chỉ đạo của người dùng và ranh giới hệ thống OncoScreen-AI.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import re
import sys
from bs4 import BeautifulSoup
import yaml

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

GUIDELINES_DIR = Path("vinh-data/guidelines")
RAW_DATA_DIR = Path("vinh-data/raw_data")
MANIFEST_PATH = GUIDELINES_DIR / "_manifest.jsonl"

USPSTF_CONFIGS = [
    {
        "slug": "breast-uspstf-2024-screening",
        "html_path": RAW_DATA_DIR / "breast/uspstf/2024/uspstf_breast_screening_2024.html",
        "cancer_type": "breast",
        "gender": "female",
        "risk_level": "average",
        "source_en": "USPSTF 2024 — Breast Cancer Screening Recommendation Statement",
        "source_vn": "USPSTF 2024 — Khuyến nghị Tầm soát Ung Thư Vú",
        "url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/breast-cancer-screening",
        "title_en": "Breast Cancer: Screening",
        "title_vn": "Tầm soát Ung Thư Vú",
        "year": "2024",
    },
    {
        "slug": "cervical-uspstf-2018-screening",
        "html_path": RAW_DATA_DIR / "cervical/uspstf/2018/uspstf_cervical_screening_2018.html",
        "cancer_type": "cervical",
        "gender": "female",
        "risk_level": "average",
        "source_en": "USPSTF 2018 — Cervical Cancer Screening Recommendation Statement",
        "source_vn": "USPSTF 2018 — Khuyến nghị Tầm soát Ung Thư Cổ Tử Cung",
        "url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/cervical-cancer-screening",
        "title_en": "Cervical Cancer: Screening",
        "title_vn": "Tầm soát Ung Thư Cổ Tử Cung",
        "year": "2018",
    },
    {
        "slug": "colorectal-uspstf-2021-screening",
        "html_path": RAW_DATA_DIR / "colorectal/uspstf/2021/uspstf_colorectal_screening_2021.html",
        "cancer_type": "colorectal",
        "gender": "any",
        "risk_level": "average",
        "source_en": "USPSTF 2021 — Colorectal Cancer Screening Recommendation Statement",
        "source_vn": "USPSTF 2021 — Khuyến nghị Tầm soát Ung Thư Đại Trực Tràng",
        "url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/colorectal-cancer-screening",
        "title_en": "Colorectal Cancer: Screening",
        "title_vn": "Tầm soát Ung Thư Đại Trực Tràng",
        "year": "2021",
    },
    {
        "slug": "lung-uspstf-2021-screening",
        "html_path": RAW_DATA_DIR / "lung/uspstf/2021/uspstf_lung_screening_2021.html",
        "cancer_type": "lung",
        "gender": "any",
        "risk_level": "high",
        "source_en": "USPSTF 2021 — Lung Cancer Screening Recommendation Statement",
        "source_vn": "USPSTF 2021 — Khuyến nghị Tầm soát Ung Thư Phổi",
        "url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/lung-cancer-screening",
        "title_en": "Lung Cancer: Screening",
        "title_vn": "Tầm soát Ung Thư Phổi",
        "year": "2021",
    },
    {
        "slug": "prostate-uspstf-2018-screening",
        "html_path": RAW_DATA_DIR / "prostate/uspstf/2018/uspstf_prostate_screening_2018.html",
        "cancer_type": "prostate",
        "gender": "male",
        "risk_level": "average",
        "source_en": "USPSTF 2018 — Prostate Cancer Screening Recommendation Statement",
        "source_vn": "USPSTF 2018 — Khuyến nghị Tầm soát Ung Thư Tuyến Tiền Liệt",
        "url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/prostate-cancer-screening",
        "title_en": "Prostate Cancer: Screening",
        "title_vn": "Tầm soát Ung Thư Tuyến Tiền Liệt",
        "year": "2018",
    },
    {
        "slug": "other-uspstf-2019-brca-risk-assessment",
        "html_path": RAW_DATA_DIR / "other/uspstf/2019/uspstf_brca_risk_assessment_2019.html",
        "cancer_type": "other",
        "gender": "female",
        "risk_level": "high",
        "source_en": "USPSTF 2019 — BRCA-Related Cancer: Risk Assessment, Genetic Counseling, and Testing",
        "source_vn": "USPSTF 2019 — Đánh giá Nguy cơ Di truyền, Tư vấn và Xét nghiệm Gen BRCA",
        "url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/brca-related-cancer-risk-assessment-genetic-counseling-and-genetic-testing",
        "title_en": "BRCA-Related Cancer: Risk Assessment, Genetic Counseling, and Genetic Testing",
        "title_vn": "Đánh giá Nguy cơ Di truyền Đột biến Gen BRCA",
        "year": "2019",
    },
    {
        "slug": "other-uspstf-2021-oral-screening",
        "html_path": RAW_DATA_DIR / "other/uspstf/2021/uspstf_oral_screening_2021.html",
        "cancer_type": "other",
        "gender": "any",
        "risk_level": "average",
        "source_en": "USPSTF 2021 — Oral Cancer Screening Recommendation Statement",
        "source_vn": "USPSTF 2021 — Khuyến nghị Tầm soát Ung Thư Khoang Miệng",
        "url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/oral-cancer-screening",
        "title_en": "Oral Cancer: Screening",
        "title_vn": "Tầm soát Ung Thư Khoang Miệng",
        "year": "2021",
    },
    {
        "slug": "other-uspstf-2023-skin-screening",
        "html_path": RAW_DATA_DIR / "other/uspstf/2023/uspstf_skin_screening_2023.html",
        "cancer_type": "other",
        "gender": "any",
        "risk_level": "average",
        "source_en": "USPSTF 2023 — Skin Cancer Screening Recommendation Statement",
        "source_vn": "USPSTF 2023 — Khuyến nghị Tầm soát Ung Thư Da",
        "url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/skin-cancer-screening",
        "title_en": "Skin Cancer: Screening",
        "title_vn": "Tầm soát Ung Thư Da",
        "year": "2023",
    },
]


def extract_uspstf_tables(soup: BeautifulSoup) -> list[dict]:
    """Trích xuất các dòng khuyến nghị từ bảng chính của USPSTF."""
    records = []
    t = soup.find("table")
    if not t:
        return records

    for tr in t.find_all("tr")[1:]:
        tds = tr.find_all(["td", "th"])
        if len(tds) >= 3:
            pop = tds[0].get_text(" ", strip=True)
            rec = tds[1].get_text(" ", strip=True)
            grade = tds[2].get_text(" ", strip=True)
            if pop and rec and grade:
                records.append({
                    "population": pop,
                    "recommendation": rec,
                    "grade": grade,
                })
    return records


def extract_clinical_considerations(soup: BeautifulSoup) -> str:
    """Trích xuất đoạn tóm tắt thực hành lâm sàng."""
    text_blocks = []
    # Tìm Table 1 (Consumer/Clinician Guide) nếu có
    tables = soup.find_all("table")
    if len(tables) > 1:
        t1 = tables[1]
        for tr in t1.find_all("tr"):
            tds = tr.find_all(["td", "th"])
            if len(tds) >= 2:
                q = tds[0].get_text(" ", strip=True)
                a = tds[1].get_text(" ", strip=True)
                if q and a and "What" in q or "To whom" in q or "How" in q:
                    text_blocks.append(f"**{q}**\n{a}")

    if not text_blocks:
        # Lấy từ các đoạn văn bản
        for p in soup.find_all("p"):
            txt = p.get_text(" ", strip=True)
            if any(k in txt.lower() for k in ["screening interval", "screening strategy", "low-dose", "mammography", "colonoscopy", "pap test"]):
                if len(txt.split()) > 20:
                    text_blocks.append(txt)
                    if len(text_blocks) >= 3:
                        break

    return "\n\n".join(text_blocks)


def translate_recommendation_vn(pop: str, rec: str, grade: str) -> tuple[str, str, str]:
    """Chuyển đổi khuyến nghị sang tiếng Việt chuẩn y khoa OncoScreen-AI."""
    grade_desc = {
        "A": "Mức A: USPSTF khuyến cáo tầm soát. Có bằng chứng chắc chắn lợi ích thực thể vượt trội nguy cơ.",
        "B": "Mức B: USPSTF khuyến cáo tầm soát. Có bằng chứng tương đối chắc chắn lợi ích thực thể vừa đến lớn.",
        "C": "Mức C: USPSTF khuyến cáo cân nhắc cá nhân hóa. Bác sĩ và người bệnh trao đổi kỹ lưỡng dựa trên tình trạng sức khỏe và mong muốn cá nhân.",
        "D": "Mức D: USPSTF khuyến cáo KHÔNG tầm soát. Không có lợi ích thực thể hoặc nguy cơ tiềm ẩn vượt trội lợi ích.",
        "I": "Mức I (Chưa đủ bằng chứng): Bằng chứng khoa học hiện tại chưa đủ để đánh giá tương quan lợi ích và tác hại.",
    }

    p_vn = pop
    p_vn = re.sub(r"(?i)\bwomen aged 40 to 74 years\b", "Phụ nữ từ 40 đến 74 tuổi", p_vn)
    p_vn = re.sub(r"(?i)\bwomen 75 years or older\b", "Phụ nữ từ 75 tuổi trở lên", p_vn)
    p_vn = re.sub(r"(?i)\bwomen with dense breasts\b", "Phụ nữ có mô tuyến vú đặc", p_vn)
    p_vn = re.sub(r"(?i)\bwomen aged 21 to 65 years\b", "Phụ nữ từ 21 đến 65 tuổi", p_vn)
    p_vn = re.sub(r"(?i)\bwomen younger than 21 years\b", "Phụ nữ dưới 21 tuổi", p_vn)
    p_vn = re.sub(r"(?i)\bwomen who have had a hysterectomy\b", "Phụ nữ đã phẫu thuật cắt tử cung toàn phần", p_vn)
    p_vn = re.sub(r"(?i)\bwomen older than 65 years\b", "Phụ nữ trên 65 tuổi (đã tầm soát đầy đủ trước đó)", p_vn)
    p_vn = re.sub(r"(?i)\badults aged 50 to 75 years\b", "Người trưởng thành từ 50 đến 75 tuổi", p_vn)
    p_vn = re.sub(r"(?i)\badults aged 45 to 49 years\b", "Người trưởng thành từ 45 đến 49 tuổi", p_vn)
    p_vn = re.sub(r"(?i)\badults aged 76 to 85 years\b", "Người lớn từ 76 đến 85 tuổi", p_vn)
    p_vn = re.sub(r"(?i)\badults aged 50 to 80 years.*smoking.*", "Người từ 50 đến 80 tuổi có tiền sử hút thuốc từ 20 bao-năm (đang hút hoặc đã bỏ dưới 15 năm)", p_vn)
    p_vn = re.sub(r"(?i)\bmen aged 55 to 69 years\b", "Nam giới từ 55 đến 69 tuổi", p_vn)
    p_vn = re.sub(r"(?i)\bmen 70 years and older\b", "Nam giới từ 70 tuổi trở lên", p_vn)
    p_vn = re.sub(r"(?i)\bwomen with a personal or family history.*\b", "Phụ nữ có tiền sử bản thân hoặc gia đình mắc ung thư vú/buồng trứng hoặc đột biến gen BRCA1/2", p_vn)
    p_vn = re.sub(r"(?i)\basymptomatic adults\b", "Người trưởng thành không có triệu chứng", p_vn)

    r_vn = rec
    # Chuyển đổi một số thuật ngữ trọng yếu trong câu khuyến nghị
    r_vn = re.sub(r"(?i)\bbiennial screening mammography\b", "chụp nhũ ảnh (mammography) định kỳ mỗi 2 năm", r_vn)
    r_vn = re.sub(r"(?i)\bscreening for cervical cancer every 3 years with cervical cytology alone\b", "tầm soát định kỳ mỗi 3 năm bằng xét nghiệm tế bào học cổ tử cung (Pap smear)", r_vn)
    r_vn = re.sub(r"(?i)\bevery 5 years with high-risk human papillomavirus \(hrHPV\) testing\b", "mỗi 5 năm bằng xét nghiệm HPV nguy cơ cao đơn độc hoặc kết hợp Pap", r_vn)
    r_vn = re.sub(r"(?i)\brecommends screening for colorectal cancer\b", "khuyến cáo tầm soát ung thư đại trực tràng (bằng FIT hàng năm hoặc nội soi mỗi 10 năm)", r_vn)
    r_vn = re.sub(r"(?i)\bannual screening for lung cancer with low-dose computed tomography \(LDCT\)\b", "chụp CT liều thấp (LDCT) định kỳ hàng năm tầm soát ung thư phổi", r_vn)
    r_vn = re.sub(r"(?i)\bperiodic prostate-specific antigen \(PSA\)-based screening\b", "xét nghiệm kháng nguyên đặc hiệu tuyến tiền liệt (PSA) dựa trên trao đổi cá nhân hóa với bác sĩ", r_vn)

    g_desc = grade_desc.get(grade.strip(), f"Mức {grade}")
    return p_vn, r_vn, g_desc


def main():
    print("====================================================================")
    print("=== TẠO BỘ DỮ LIỆU GUIDELINES USPSTF (TIẾNG ANH & TIẾNG VIỆT) ===")
    print("====================================================================")

    manifest_entries = []
    generated_en = 0
    generated_vn = 0

    for cfg in USPSTF_CONFIGS:
        html_file = cfg["html_path"]
        if not html_file.exists():
            print(f"[!] Không tìm thấy tệp HTML: {html_file}")
            continue

        with open(html_file, encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        table_records = extract_uspstf_tables(soup)
        clinical_text = extract_clinical_considerations(soup)

        slug = cfg["slug"]
        cancer_type = cfg["cancer_type"]

        # -------------------------------------------------------------
        # A. BẢN TIẾNG ANH (-en.md)
        # -------------------------------------------------------------
        en_file = f"{slug}-en.md"
        en_path = GUIDELINES_DIR / en_file

        en_meta = {
            "cancer_type": cancer_type,
            "source": cfg["source_en"],
            "url": cfg["url"],
            "gender": cfg["gender"],
            "risk_level": cfg["risk_level"],
            "language": "en",
        }

        en_rec_rows = []
        for r in table_records:
            en_rec_rows.append(f"- **Population**: {r['population']}\n  - **Recommendation**: {r['recommendation']}\n  - **Grade**: **{r['grade']}**")
        en_rec_section = "\n\n".join(en_rec_rows) if en_rec_rows else "No tabular recommendations parsed."

        en_body = f"""## USPSTF Recommendation Summary
The United States Preventive Services Task Force (USPSTF) provides evidence-based recommendations on clinical preventive services. Below are the definitive screening recommendations for {cfg['title_en']}:

{en_rec_section}

## Clinical Considerations & Implementation
{clinical_text if clinical_text else "Clinicians should review individual patient risk factors, screening intervals, and shared decision-making considerations."}

## Rationale and Balance of Benefits and Harms
Screening effectiveness depends on disease prevalence, test accuracy, interval adherence, and the balance between early detection mortality benefits and potential screening harms (false positives, unnecessary biopsies, overdiagnosis).
"""

        en_yaml = yaml.safe_dump(en_meta, allow_unicode=True, sort_keys=False)
        en_content = f"---\n{en_yaml}---\n{en_body.strip()}\n"
        en_path.write_text(en_content, encoding="utf-8")
        generated_en += 1

        sec_count_en = len([l for l in en_body.splitlines() if l.startswith("## ")])
        manifest_entries.append({
            "file": en_file,
            "language": "en",
            "cancer_type": cancer_type,
            "source": cfg["source_en"],
            "url": cfg["url"],
            "gender": cfg["gender"],
            "risk_level": cfg["risk_level"],
            "sections_count": sec_count_en,
            "created_at": dt.datetime.now().strftime("%Y-%m-%d"),
        })

        # -------------------------------------------------------------
        # B. BẢN TIẾNG VIỆT (-vn.md)
        # -------------------------------------------------------------
        vn_file = f"{slug}-vn.md"
        vn_path = GUIDELINES_DIR / vn_file

        vn_meta = {
            "cancer_type": cancer_type,
            "source": cfg["source_vn"],
            "url": cfg["url"],
            "gender": cfg["gender"],
            "risk_level": cfg["risk_level"],
            "language": "vi",
        }

        vn_rec_rows = []
        for r in table_records:
            p_vn, r_vn, g_vn = translate_recommendation_vn(r["population"], r["recommendation"], r["grade"])
            vn_rec_rows.append(f"- **Nhóm đối tượng**: {p_vn}\n  - **Khuyến nghị**: {r_vn}\n  - **Mức độ khuyến cáo**: **{r['grade']}** — {g_vn}")
        vn_rec_section = "\n\n".join(vn_rec_rows) if vn_rec_rows else "Không trích xuất được bảng khuyến nghị."

        vn_body = f"""## Tóm tắt Khuyến nghị Tầm soát USPSTF
Lực lượng Đặc nhiệm Y tế Dự phòng Hoa Kỳ (USPSTF) đưa ra các khuyến nghị dựa trên bằng chứng khoa học thực nghiệm. Dưới đây là các tiêu chuẩn tầm soát cho {cfg['title_vn']}:

{vn_rec_section}

## Thực hành Lâm sàng & Đối tượng Áp dụng
{clinical_text if clinical_text else "Bác sĩ cần đánh giá kỹ các yếu tố nguy cơ của người bệnh, khoảng cách giữa các lần xét nghiệm và tiến hành trao đổi quyết định cá nhân hóa."}

## Cơ sở Khoa học, Lợi ích và Nguy cơ Tiềm ẩn
Hiệu quả của việc tầm soát phụ thuộc vào tần suất mắc bệnh trong cộng đồng, độ nhạy/độ đặc hiệu của xét nghiệm, và sự cân bằng giữa lợi ích giảm tử vong với các nguy cơ tiềm ẩn (kết quả dương tính giả gây lo lắng, sinh thiết không cần thiết, chẩn đoán quá mức).
"""

        vn_yaml = yaml.safe_dump(vn_meta, allow_unicode=True, sort_keys=False)
        vn_content = f"---\n{vn_yaml}---\n{vn_body.strip()}\n"
        vn_path.write_text(vn_content, encoding="utf-8")
        generated_vn += 1

        sec_count_vn = len([l for l in vn_body.splitlines() if l.startswith("## ")])
        manifest_entries.append({
            "file": vn_file,
            "language": "vi",
            "cancer_type": cancer_type,
            "source": cfg["source_vn"],
            "url": cfg["url"],
            "gender": cfg["gender"],
            "risk_level": cfg["risk_level"],
            "sections_count": sec_count_vn,
            "created_at": dt.datetime.now().strftime("%Y-%m-%d"),
        })

        print(f" [+] Đã tạo: {en_file} (EN) & {vn_file} (VN)")

    # -------------------------------------------------------------
    # C. CẬP NHẬT _MANIFEST.JSONL
    # -------------------------------------------------------------
    # Đọc manifest hiện có để nối thêm không trùng lặp
    existing_manifest = []
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            existing_manifest = [json.loads(line) for line in f if line.strip()]

    existing_files = {e["file"] for e in existing_manifest}
    added_count = 0
    for entry in manifest_entries:
        if entry["file"] not in existing_files:
            existing_manifest.append(entry)
            existing_files.add(entry["file"])
            added_count += 1

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        for entry in existing_manifest:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print("\n====================================================================")
    print(f"[✓] HOÀN TẤT TẠO GUIDELINES USPSTF:")
    print(f"    - Bản tiếng Anh tạo mới (-en.md) : {generated_en} tệp")
    print(f"    - Bản tiếng Việt tạo mới (-vn.md) : {generated_vn} tệp")
    print(f"    - Đã bổ sung vào manifest        : {added_count} bản ghi")
    print(f"    - Tổng số bản ghi trong manifest  : {len(existing_manifest)}")
    print("====================================================================")


if __name__ == "__main__":
    main()
