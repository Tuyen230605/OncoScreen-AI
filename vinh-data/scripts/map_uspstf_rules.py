#!/usr/bin/env python3
"""USPSTF RULE ADAPTER SCRIPT (Calibration Point 1).

Chuyển đổi (map) các khuyến nghị USPSTF thô thành đúng schema của `screening_rules.json`
đáp ứng đầy đủ các ràng buộc kiến trúc của OncoScreen-AI:
- camelCase (USPSTF API: ageRange, sex, servFreq, grade) -> snake_case (min_age, max_age, gender, interval_months).
- Liên kết với mã dịch vụ trong `services.json`.
- Tương thích 100% với Pydantic Rule model trong `ai_core.tools.eligibility`.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

OUTPUT_RULES_PATH = Path(__file__).resolve().parent.parent / "uspstf_mapped_rules.json"

# Dữ liệu mô phỏng cấu trúc USPSTF API JSON thô (camelCase)
USPSTF_RAW_RECOMMENDATIONS = [
    {
        "topicId": "breast_cancer_screening",
        "cancerType": "breast",
        "title": "Breast Cancer: Screening",
        "specificRecommendations": [
            {
                "recId": "breast_40_74",
                "population": "Women aged 40 to 74 years",
                "sex": "female",
                "ageRange": [40, 74],
                "grade": "B",
                "servFreq": "biennial",
                "servFreqMonths": 24,
                "clinicalMethodEn": "Screening mammography",
                "clinicalMethodVi": "Chụp nhũ ảnh (mammography)",
                "riskFactorsRequired": [],
                "familyHistoryNoteVi": "Có người thân mắc ung thư vú: guideline nguy cơ trung bình có thể không đủ; bác sĩ cần đánh giá kế hoạch riêng.",
                "appliesBecauseVi": "Phụ nữ 40–74 tuổi",
                "docId": "breast_uspstf_2024",
                "section": "Khuyến nghị",
                "serviceCode": "breast_screening",
            }
        ],
    },
    {
        "topicId": "cervical_cancer_screening",
        "cancerType": "cervical",
        "title": "Cervical Cancer: Screening",
        "specificRecommendations": [
            {
                "recId": "cervical_21_29",
                "population": "Women aged 21 to 29 years",
                "sex": "female",
                "ageRange": [21, 29],
                "grade": "A",
                "servFreq": "every 3 years",
                "servFreqMonths": 36,
                "clinicalMethodEn": "Cervical cytology alone (Pap smear)",
                "clinicalMethodVi": "Xét nghiệm tế bào học cổ tử cung (Pap)",
                "riskFactorsRequired": [],
                "familyHistoryNoteVi": None,
                "appliesBecauseVi": "Phụ nữ 21–29 tuổi",
                "docId": "cervical_uspstf_2018",
                "section": "Khuyến nghị",
                "serviceCode": "cervical_screening",
            },
            {
                "recId": "cervical_30_65",
                "population": "Women aged 30 to 65 years",
                "sex": "female",
                "ageRange": [30, 65],
                "grade": "A",
                "servFreq": "every 5 years",
                "servFreqMonths": 60,
                "clinicalMethodEn": "hrHPV testing alone or cotesting every 5 years (or Pap every 3 years)",
                "clinicalMethodVi": "Xét nghiệm HPV nguy cơ cao (hoặc Pap mỗi 3 năm)",
                "riskFactorsRequired": [],
                "familyHistoryNoteVi": None,
                "appliesBecauseVi": "Phụ nữ 30–65 tuổi",
                "docId": "cervical_uspstf_2018",
                "section": "Khuyến nghị",
                "serviceCode": "cervical_screening",
            },
        ],
    },
    {
        "topicId": "colorectal_cancer_screening",
        "cancerType": "colorectal",
        "title": "Colorectal Cancer: Screening",
        "specificRecommendations": [
            {
                "recId": "colorectal_45_75",
                "population": "Adults aged 45 to 75 years",
                "sex": "any",
                "ageRange": [45, 75],
                "grade": "A",
                "servFreq": "annual (FIT) or 10 years (colonoscopy)",
                "servFreqMonths": 12,
                "clinicalMethodEn": "Stool-based tests (FIT annual) or colonoscopy every 10 years",
                "clinicalMethodVi": "Xét nghiệm FIT (hoặc nội soi đại tràng mỗi 10 năm)",
                "riskFactorsRequired": [],
                "familyHistoryNoteVi": "Có người thân mắc ung thư đại trực tràng: thường cần bắt đầu sớm hơn và chọn phương pháp riêng; bác sĩ quyết định.",
                "appliesBecauseVi": "Người 45–75 tuổi",
                "docId": "colorectal_uspstf_2021",
                "section": "Khuyến nghị",
                "serviceCode": "colorectal_screening",
            }
        ],
    },
    {
        "topicId": "lung_cancer_screening",
        "cancerType": "lung",
        "title": "Lung Cancer: Screening",
        "specificRecommendations": [
            {
                "recId": "lung_50_80_20py",
                "population": "Adults aged 50 to 80 years with 20 pack-year smoking history",
                "sex": "any",
                "ageRange": [50, 80],
                "grade": "B",
                "servFreq": "annual",
                "servFreqMonths": 12,
                "clinicalMethodEn": "Low-dose computed tomography (LDCT)",
                "clinicalMethodVi": "Chụp CT phổi liều thấp (LDCT)",
                "riskFactorsRequired": ["pack_years>=20"],
                "familyHistoryNoteVi": None,
                "appliesBecauseVi": "Người 50–80 tuổi, hút thuốc từ 20 gói-năm (còn hút hoặc bỏ dưới 15 năm)",
                "docId": "lung_uspstf_2021",
                "section": "Khuyến nghị",
                "serviceCode": "lung_screening",
            }
        ],
    },
    {
        "topicId": "prostate_cancer_screening",
        "cancerType": "prostate",
        "title": "Prostate Cancer: Screening",
        "specificRecommendations": [
            {
                "recId": "prostate_55_69_sdm",
                "population": "Men aged 55 to 69 years",
                "sex": "male",
                "ageRange": [55, 69],
                "grade": "C",
                "servFreq": "individualized",
                "servFreqMonths": None,
                "clinicalMethodEn": "Periodic PSA-based screening with shared decision-making",
                "clinicalMethodVi": "Trao đổi với bác sĩ về xét nghiệm PSA (quyết định cá nhân)",
                "riskFactorsRequired": [],
                "familyHistoryNoteVi": "Có người thân mắc ung thư tuyến tiền liệt: nguy cơ cao hơn, cần bác sĩ tư vấn riêng.",
                "appliesBecauseVi": "Nam giới 55–69 tuổi",
                "docId": "prostate_uspstf_2018",
                "section": "Khuyến nghị",
                "serviceCode": "prostate_screening",
            }
        ],
    },
]


def map_uspstf_to_oncoscreen_rules(uspstf_data: list[dict]) -> dict:
    """Hàm adapter chuyển đổi schema USPSTF sang screening_rules.json."""
    mapped_rules = []

    for topic in uspstf_data:
        cancer_type = topic["cancerType"]
        for spec in topic["specificRecommendations"]:
            # Chỉ map các khuyến nghị tầm soát Grade A, B, C (bỏ qua Grade D không tầm soát)
            if spec.get("grade") not in ("A", "B", "C"):
                continue

            age_range = spec.get("ageRange", [0, 120])
            min_age = age_range[0] if len(age_range) >= 1 else 0
            max_age = age_range[1] if len(age_range) >= 2 else 120

            # Ánh xạ snake_case
            rule = {
                "id": spec["recId"],
                "cancer_type": cancer_type,
                "doc_id": spec["docId"],
                "section": spec["section"],
                "gender": spec["sex"],
                "min_age": min_age,
                "max_age": max_age,
                "requires": spec.get("riskFactorsRequired", []),
                "method": spec["clinicalMethodVi"],
                "start_age": min_age,
                "interval_months": spec.get("servFreqMonths"),
                "applies_because": spec["appliesBecauseVi"],
                "family_note": spec.get("familyHistoryNoteVi"),
                "_uspstf_metadata": {
                    "grade": spec.get("grade"),
                    "serv_freq": spec.get("servFreq"),
                    "service_code": spec.get("serviceCode"),
                    "method_en": spec.get("clinicalMethodEn"),
                },
            }
            mapped_rules.append(rule)

    return {
        "version": "1.0-uspstf-adapter",
        "description": "Rules converted from USPSTF recommendations using map_uspstf_rules.py",
        "rules": mapped_rules,
    }


def main():
    print("====================================================================")
    print("=== USPSTF RULE ADAPTER SCRIPT (Calibration Point 1) ===")
    print("====================================================================")

    res = map_uspstf_to_oncoscreen_rules(USPSTF_RAW_RECOMMENDATIONS)
    print(f"[*] Đã chuyển đổi {len(res['rules'])} quy tắc từ cấu trúc USPSTF sang schema OncoScreen-AI:")

    for r in res["rules"]:
        print(f"  - [{r['id']}] {r['cancer_type'].upper()} ({r['gender']}, {r['min_age']}-{r['max_age']} tuổi) | Grade: {r['_uspstf_metadata']['grade']} -> {r['method']}")

    OUTPUT_RULES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_RULES_PATH, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)

    print(f"\n[✓] Đã lưu tệp quy tắc đã chuyển đổi tại: {OUTPUT_RULES_PATH}")

    # Kiểm tra tính tương thích với Pydantic Rule schema của ai_core nếu có
    try:
        from ai_core.schemas import CancerType
        from ai_core.tools.eligibility import Rule, source_for
        validated = 0
        for r in res["rules"]:
            core_fields = {k: v for k, v in r.items() if not k.startswith("_")}
            rule_obj = Rule(
                id=core_fields["id"],
                cancer_type=CancerType(core_fields["cancer_type"]),
                doc_id=core_fields["doc_id"],
                section=core_fields["section"],
                gender=core_fields["gender"],
                min_age=int(core_fields["min_age"]),
                max_age=core_fields.get("max_age"),
                requires=tuple(core_fields.get("requires", [])),
                method=core_fields["method"],
                start_age=core_fields.get("start_age"),
                interval_months=core_fields.get("interval_months"),
                applies_because=core_fields["applies_because"],
                family_note=core_fields.get("family_note"),
                source=source_for(core_fields["doc_id"], core_fields["section"]),
            )
            validated += 1
        print(f"[✓] Kiểm chứng Pydantic Rule: 100% ({validated}/{len(res['rules'])}) quy tắc hợp lệ tuyệt đối!")
    except Exception as e:
        print(f"[!] Lỗi kiểm chứng: {e}")


if __name__ == "__main__":
    main()
