"""Crawler script to fetch and organize raw guideline datasets into ai_core/data/raw_data/.

Conforms strictly to the raw_data structure:
raw_data/
└── <cancer_type>/
    └── <publisher>/
        └── <year>/
            ├── <publisher>_<topic>_<year>.<ext>
            └── source.yaml
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
import urllib.request
import pyarrow.parquet as pq

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

RAW_DATA_DIR = Path("ai_core/data/raw_data")
TODAY = date.today().isoformat()

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def write_source_yaml(
    path: Path,
    publisher: str,
    title: str,
    url: str,
    publication_date: str,
    version: str,
    jurisdiction: str,
    language: str,
    license_str: str,
    reuse_notes: str,
    target_file: Path,
) -> None:
    sha = sha256_file(target_file) if target_file.exists() else ""
    content = f"""# Metadata nguồn theo chuẩn OncoScreen-AI
publisher: "{publisher}"
title: "{title}"
url: "{url}"
publication_date: "{publication_date}"
version: "{version}"
accessed_on: "{TODAY}"
jurisdiction: "{jurisdiction}"
language: "{language}"
license: "{license_str}"
reuse_notes: "{reuse_notes}"
sha256: "{sha}"
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def download_url(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                f.write(data)
            return True
    except Exception as e:
        print(f"[!] Lỗi tải {url}: {e}")
        return False


# ==============================================================================
# 1. USPSTF Cancer Screening Recommendations
# ==============================================================================
USPSTF_TOPICS = [
    {
        "cancer_type": "breast",
        "year": "2024",
        "title": "Breast Cancer: Screening",
        "url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/breast-cancer-screening",
        "filename": "uspstf_breast_screening_2024.html",
        "publication_date": "2024-04-30",
        "version": "Final Recommendation Statement (2024)",
    },
    {
        "cancer_type": "colorectal",
        "year": "2021",
        "title": "Colorectal Cancer: Screening",
        "url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/colorectal-cancer-screening",
        "filename": "uspstf_colorectal_screening_2021.html",
        "publication_date": "2021-05-18",
        "version": "Final Recommendation Statement (2021)",
    },
    {
        "cancer_type": "cervical",
        "year": "2018",
        "title": "Cervical Cancer: Screening",
        "url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/cervical-cancer-screening",
        "filename": "uspstf_cervical_screening_2018.html",
        "publication_date": "2018-08-21",
        "version": "Final Recommendation Statement (2018)",
    },
    {
        "cancer_type": "lung",
        "year": "2021",
        "title": "Lung Cancer: Screening",
        "url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/lung-cancer-screening",
        "filename": "uspstf_lung_screening_2021.html",
        "publication_date": "2021-03-09",
        "version": "Final Recommendation Statement (2021)",
    },
    {
        "cancer_type": "prostate",
        "year": "2018",
        "title": "Prostate Cancer: Screening",
        "url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/prostate-cancer-screening",
        "filename": "uspstf_prostate_screening_2018.html",
        "publication_date": "2018-05-08",
        "version": "Final Recommendation Statement (2018)",
    },
    {
        "cancer_type": "other",
        "year": "2019",
        "title": "BRCA-Related Cancer: Risk Assessment, Genetic Counseling, and Genetic Testing",
        "url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/brca-related-cancer-risk-assessment-genetic-counseling-and-genetic-testing",
        "filename": "uspstf_brca_risk_assessment_2019.html",
        "publication_date": "2019-08-20",
        "version": "Final Recommendation Statement (2019)",
    },
    {
        "cancer_type": "other",
        "year": "2023",
        "title": "Skin Cancer: Screening",
        "url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/skin-cancer-screening",
        "filename": "uspstf_skin_screening_2023.html",
        "publication_date": "2023-04-18",
        "version": "Final Recommendation Statement (2023)",
    },
    {
        "cancer_type": "other",
        "year": "2021",
        "title": "Oral Cancer: Screening",
        "url": "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/oral-cancer-screening",
        "filename": "uspstf_oral_screening_2021.html",
        "publication_date": "2021-08-24",
        "version": "Final Recommendation Statement (2021)",
    },
]


def crawl_uspstf() -> None:
    print("\n=== [1/4] Crawling USPSTF Recommendations ===")
    for item in USPSTF_TOPICS:
        target_dir = RAW_DATA_DIR / item["cancer_type"] / "uspstf" / item["year"]
        target_file = target_dir / item["filename"]
        source_yaml = target_dir / "source.yaml"

        print(f" -> Đang tải USPSTF: {item['title']} ({item['cancer_type']})...")
        if not target_file.exists():
            download_url(item["url"], target_file)
        else:
            print(f"    (Đã tồn tại: {target_file})")

        write_source_yaml(
            path=source_yaml,
            publisher="USPSTF (U.S. Preventive Services Task Force)",
            title=item["title"],
            url=item["url"],
            publication_date=item["publication_date"],
            version=item["version"],
            jurisdiction="US",
            language="en",
            license_str="Public Domain / U.S. Government Work",
            reuse_notes="Khuyến nghị tầm soát lâm sàng chính thức của USPSTF",
            target_file=target_file,
        )


# ==============================================================================
# 2. NCI PDQ Screening Summaries (National Cancer Institute)
# ==============================================================================
NCI_PDQ_TOPICS = [
    {
        "cancer_type": "breast",
        "year": "2024",
        "title": "Breast Cancer Screening (PDQ®) – Health Professional Version",
        "url": "https://www.cancer.gov/types/breast/hp/breast-screening-pdq",
        "filename": "nci_pdq_breast_screening_2024.html",
    },
    {
        "cancer_type": "colorectal",
        "year": "2024",
        "title": "Colorectal Cancer Screening (PDQ®) – Health Professional Version",
        "url": "https://www.cancer.gov/types/colorectal/hp/colorectal-screening-pdq",
        "filename": "nci_pdq_colorectal_screening_2024.html",
    },
    {
        "cancer_type": "cervical",
        "year": "2024",
        "title": "Cervical Cancer Screening (PDQ®) – Health Professional Version",
        "url": "https://www.cancer.gov/types/cervical/hp/cervical-screening-pdq",
        "filename": "nci_pdq_cervical_screening_2024.html",
    },
    {
        "cancer_type": "lung",
        "year": "2024",
        "title": "Lung Cancer Screening (PDQ®) – Health Professional Version",
        "url": "https://www.cancer.gov/types/lung/hp/lung-screening-pdq",
        "filename": "nci_pdq_lung_screening_2024.html",
    },
    {
        "cancer_type": "liver",
        "year": "2024",
        "title": "Liver (Hepatocellular) Cancer Screening (PDQ®) – Health Professional Version",
        "url": "https://www.cancer.gov/types/liver/hp/liver-screening-pdq",
        "filename": "nci_pdq_liver_screening_2024.html",
    },
    {
        "cancer_type": "prostate",
        "year": "2024",
        "title": "Prostate Cancer Screening (PDQ®) – Health Professional Version",
        "url": "https://www.cancer.gov/types/prostate/hp/prostate-screening-pdq",
        "filename": "nci_pdq_prostate_screening_2024.html",
    },
    {
        "cancer_type": "other",
        "year": "2024",
        "title": "Esophageal Cancer Screening (PDQ®) – Health Professional Version",
        "url": "https://www.cancer.gov/types/esophageal/hp/esophageal-screening-pdq",
        "filename": "nci_pdq_esophageal_screening_2024.html",
    },
    {
        "cancer_type": "other",
        "year": "2024",
        "title": "Stomach (Gastric) Cancer Screening (PDQ®) – Health Professional Version",
        "url": "https://www.cancer.gov/types/stomach/hp/stomach-screening-pdq",
        "filename": "nci_pdq_stomach_screening_2024.html",
    },
    {
        "cancer_type": "other",
        "year": "2024",
        "title": "Oral Cavity and Nasopharyngeal Cancer Screening (PDQ®) – Health Professional Version",
        "url": "https://www.cancer.gov/types/head-and-neck/hp/oral-screening-pdq",
        "filename": "nci_pdq_oral_screening_2024.html",
    },
]


def crawl_nci_pdq() -> None:
    print("\n=== [2/4] Crawling NCI PDQ Screening Summaries ===")
    for item in NCI_PDQ_TOPICS:
        target_dir = RAW_DATA_DIR / item["cancer_type"] / "nci" / item["year"]
        target_file = target_dir / item["filename"]
        source_yaml = target_dir / "source.yaml"

        print(f" -> Đang tải NCI PDQ: {item['title']} ({item['cancer_type']})...")
        if not target_file.exists():
            download_url(item["url"], target_file)
        else:
            print(f"    (Đã tồn tại: {target_file})")

        write_source_yaml(
            path=source_yaml,
            publisher="National Cancer Institute (NCI)",
            title=item["title"],
            url=item["url"],
            publication_date=f"{item['year']}-01-01",
            version="PDQ Information Summaries",
            jurisdiction="US",
            language="en",
            license_str="Public Domain / NCI PDQ®",
            reuse_notes="Bản tóm tắt thông tin tầm soát ung thư dành cho cán bộ y tế (Health Professional)",
            target_file=target_file,
        )


# ==============================================================================
# 3. NCI CancerGov_QA (Hugging Face) -> Partitioned by cancer_type
# ==============================================================================
FOCUS_TO_CANCER: dict[str, str] = {
    "Breast Cancer": "breast",
    "Cervical Cancer": "cervical",
    "Colorectal Cancer": "colorectal",
    "Colon Cancer": "colorectal",
    "Rectal Cancer": "colorectal",
    "Non-Small Cell Lung Cancer": "lung",
    "Small Cell Lung Cancer": "lung",
    "Adult Primary Liver Cancer": "liver",
    "Childhood Liver Cancer": "liver",
    "Prostate Cancer": "prostate",
}


def partition_cancergov_qa() -> None:
    print("\n=== [3/4] Partitioning CancerGov_QA into raw_data hierarchy ===")
    parquet_path = RAW_DATA_DIR / "CancerGov_QA.parquet"
    if not parquet_path.exists():
        print(f"[!] Không tìm thấy {parquet_path}")
        return

    table = pq.read_table(parquet_path)
    records = table.to_pylist()
    print(f" -> Đọc được {len(records)} QA items từ CancerGov_QA.parquet")

    grouped: dict[str, list[dict]] = {}
    for r in records:
        focus = r.get("focus", "")
        ctype = FOCUS_TO_CANCER.get(focus, "other")
        grouped.setdefault(ctype, []).append(r)

    for ctype, items in grouped.items():
        target_dir = RAW_DATA_DIR / ctype / "nci" / "2023"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"nci_cancergov_qa_{ctype}_2023.jsonl"
        source_yaml = target_dir / "source.yaml"

        print(f" -> Ghi {len(items)} câu hỏi-đáp vào {target_file}")
        with open(target_file, "w", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")

        # Ghi metadata nếu chưa có hoặc cập nhật cho JSONL
        write_source_yaml(
            path=source_yaml,
            publisher="National Cancer Institute (NCI) / Pedrampedram",
            title=f"CancerGov_QA — {ctype.title()} Cancer PDQ QA Dataset",
            url="https://huggingface.co/datasets/Pedrampedram/CancerGov_QA",
            publication_date="2023-04-26",
            version="1.0.0",
            jurisdiction="US",
            language="en",
            license_str="Public Domain / NCI PDQ®",
            reuse_notes="Tập dữ liệu câu hỏi - trả lời trích xuất từ các bản tóm tắt NCI PDQ",
            target_file=target_file,
        )


# ==============================================================================
# 4. MedGUIDE_MCQA_8K (NCCN Decision Trees from Hugging Face)
# ==============================================================================
MEDGUIDE_TO_CANCER: dict[str, str] = {
    "bre": "breast",
    "cer": "cervical",
    "col": "colorectal",
    "nscl": "lung",
    "sclc": "lung",
    "hcc": "liver",
    "prostate": "prostate",
}


def partition_medguide_nccn() -> None:
    print("\n=== [4/4] Partitioning MedGUIDE (NCCN Decision Trees) into raw_data ===")
    parquet_path = RAW_DATA_DIR / "MedGUIDE_MCQA_8K.parquet"
    if not parquet_path.exists():
        print(f"[!] Không tìm thấy {parquet_path}")
        return

    table = pq.read_table(parquet_path)
    records = table.to_pylist()
    print(f" -> Đọc được {len(records)} ca lâm sàng từ MedGUIDE_MCQA_8K.parquet")

    grouped: dict[str, list[dict]] = {}
    for r in records:
        disease = str(r.get("disease", ""))
        prefix = disease.split("_")[0].lower()
        if prefix.startswith("bre"):
            ctype = "breast"
        elif prefix.startswith("cer"):
            ctype = "cervical"
        elif prefix.startswith("col"):
            ctype = "colorectal"
        elif prefix.startswith("nscl") or prefix.startswith("sclc"):
            ctype = "lung"
        elif prefix.startswith("hcc"):
            ctype = "liver"
        elif prefix.startswith("prostate"):
            ctype = "prostate"
        else:
            ctype = "other"
        grouped.setdefault(ctype, []).append(r)

    for ctype, items in grouped.items():
        target_dir = RAW_DATA_DIR / ctype / "nccn" / "2025"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"nccn_medguide_{ctype}_2025.jsonl"
        source_yaml = target_dir / "source.yaml"

        print(f" -> Ghi {len(items)} ca quyết định lâm sàng NCCN vào {target_file}")
        with open(target_file, "w", encoding="utf-8") as f:
            for it in items:
                # Lưu gọn các trường quan trọng cho RAG/Copilot
                clean_it = {
                    "disease": it.get("disease"),
                    "path": it.get("path"),
                    "profile": it.get("profile"),
                    "answer_text": it.get("answer_text"),
                    "prompt": it.get("prompt"),
                    "options": it.get("options"),
                }
                f.write(json.dumps(clean_it, ensure_ascii=False) + "\n")

        write_source_yaml(
            path=source_yaml,
            publisher="NCCN (National Comprehensive Cancer Network) / MedGUIDE",
            title=f"MedGUIDE NCCN Decision Guidelines — {ctype.title()}",
            url="https://huggingface.co/datasets/MedGUIDE/MedGUIDE-MCQA-8K",
            publication_date="2025-05-15",
            version="MCQA-8K",
            jurisdiction="US",
            language="en",
            license_str="Research and Educational Guideline Dataset",
            reuse_notes="Lưu đồ quyết định lâm sàng NCCN cho chẩn đoán và phân tầng nguy cơ ung thư",
            target_file=target_file,
        )


def main() -> None:
    print("==================================================================")
    print(" BẮT ĐẦU CRAWL & ĐÓNG GÓI DỮ LIỆU NGUỒN CHO ONCOSCREEN-AI RAW_DATA")
    print("==================================================================")
    crawl_uspstf()
    crawl_nci_pdq()
    partition_cancergov_qa()
    partition_medguide_nccn()
    print("\n[V] ĐÃ HOÀN TẤT CRAWL VÀ TỔ CHỨC DỮ LIỆU THÀNH CÔNG VÀO RAW_DATA!")


if __name__ == "__main__":
    main()
