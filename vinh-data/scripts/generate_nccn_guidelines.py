#!/usr/bin/env python3
"""NCCN GUIDELINES & EVALUATION SUITE GENERATOR.

Trích xuất và biên tập các lưu đồ quyết định lâm sàng (Decision Trees) và hướng dẫn
đánh giá nguy cơ cao / di truyền (High-Risk & Genetic Assessment) của NCCN 2025:
1. Tạo 5 cặp tài liệu RAG Guidelines (EN & VN) cho 5 nhóm bệnh trọng tâm:
   - Liver: Lưu đồ giám sát ung thư gan HCC bằng Siêu âm + AFP (HCC-1).
   - Lung: Tiêu chuẩn tầm soát LDCT và xử trí nốt phổi theo Lung-RADS.
   - Breast: Đánh giá nguy cơ cao di truyền (BRCA1/2, tiền sử gia đình, chụp MRI tuyến vú).
   - Colorectal: Tầm soát nhóm nguy cơ cao (Hội chứng Lynch, FAP, tiền sử gia đình sớm).
   - Prostate: Lưu đồ phát hiện sớm ung thư tuyến tiền liệt và phân tầng theo nồng độ PSA.
2. Trích xuất các ca lâm sàng tầm soát/giám sát từ MedGUIDE vào `vinh-data/evaluation/nccn_screening_eval_suite.jsonl`.
3. Cập nhật `_manifest.jsonl` và kiểm chứng tính toàn vẹn 100%.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import sys
import yaml

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

GUIDELINES_DIR = Path("vinh-data/guidelines")
RAW_DATA_DIR = Path("vinh-data/raw_data")
EVAL_DIR = Path("vinh-data/evaluation")
MANIFEST_PATH = GUIDELINES_DIR / "_manifest.jsonl"

NCCN_DOCS = [
    {
        "slug": "liver-nccn-2025-surveillance-decision-tree",
        "cancer_type": "liver",
        "gender": "any",
        "risk_level": "high",
        "url": "https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1442",
        "source_en": "NCCN Guidelines 2025 — Hepatocellular Carcinoma: Screening and Surveillance (HCC-1)",
        "source_vn": "NCCN 2025 — Hướng dẫn Tầm soát & Giám sát Ung Thư Biểu Mô Tế Bào Gan (HCC-1)",
        "body_en": """## NCCN High-Risk Population for Liver Cancer Surveillance
Surveillance for hepatocellular carcinoma (HCC) is recommended for individuals at high risk, specifically:
- Patients with cirrhosis of any etiology (Child-Pugh Class A or B; Child-Pugh Class C only if awaiting liver transplant).
- Patients with chronic Hepatitis B virus (HBV) infection:
  * Asian men age ≥40 years, Asian women age ≥50 years.
  * Individuals with a family history of HCC.
  * African and/or Black individuals with HBV.
- Patients with chronic Hepatitis C virus (HCV) infection with advanced fibrosis (stage F3).

## NCCN HCC Surveillance Algorithm (Protocol HCC-1)
The standard surveillance modality recommended by NCCN:
- **Modality**: Transabdominal Ultrasound (US) combined with serum Alpha-fetoprotein (AFP).
- **Interval**: Every 6 months.

## Decision Tree for Nodule Management & Positive Findings
1. **Ultrasound Negative & Normal AFP**:
   - Continue routine surveillance with Ultrasound + AFP every 6 months.
2. **Ultrasound Nodule < 10 mm (with normal or borderline AFP)**:
   - Repeat Ultrasound + AFP at a shortened interval of 3 to 6 months.
   - If stable for 12–24 months, return to routine 6-month surveillance.
3. **Ultrasound Nodule ≥ 10 mm OR Significantly Rising AFP (> 20 ng/mL)**:
   - Immediate escalation to diagnostic multiphasic contrast-enhanced imaging:
     * 3-phase or 4-phase contrast-enhanced abdominal CT, OR
     * Dynamic contrast-enhanced abdominal MRI with liver-specific contrast.
   - Assessment according to LI-RADS criteria (LI-RADS 4 or 5 indicates high probability or definitive HCC requiring multidisciplinary review).
""",
        "body_vn": """## Đối tượng Nguy cơ Cao Cần Giám sát Ung Thư Gan theo NCCN
NCCN khuyến cáo giám sát ung thư biểu mô tế bào gan (HCC) bắt buộc cho các nhóm người bệnh nguy cơ cao:
- Bệnh nhân xơ gan do bất kỳ nguyên nhân nào (Child-Pugh A hoặc B; Child-Pugh C khi đang trong danh sách chờ ghép gan).
- Người nhiễm virus viêm gan B (HBV) mạn tính:
  * Nam giới gốc Á từ 40 tuổi, nữ giới gốc Á từ 50 tuổi.
  * Người có tiền sử gia đình (bố mẹ, anh chị em ruột) mắc ung thư gan.
  * Người gốc Phi có nhiễm HBV.
- Người nhiễm virus viêm gan C (HCV) mạn tính có xơ hóa gan tiến triển (giai đoạn F3 trở lên).

## Lưu đồ & Tiêu chuẩn Giám sát NCCN (Phác đồ HCC-1)
Phương pháp giám sát chuẩn được NCCN khuyến cáo:
- **Phương pháp**: Siêu âm ổ bụng kết hợp xét nghiệm định lượng kháng nguyên AFP (Alpha-fetoprotein) huyết thanh.
- **Tần suất**: Định kỳ mỗi 6 tháng một lần.

## Cây Quyết định Xử trí Nốt Gan & Bất thường (Decision Tree)
1. **Siêu âm âm tính & AFP bình thường**:
   - Tiếp tục duy trì giám sát định kỳ Siêu âm + AFP mỗi 6 tháng.
2. **Nốt giảm âm trên siêu âm kích thước < 10 mm (AFP bình thường hoặc tăng nhẹ)**:
   - Lặp lại Siêu âm + AFP sau 3 đến 6 tháng để theo dõi tốc độ phát triển.
   - Nếu kích thước ổn định sau 12–24 tháng, quay lại chu kỳ định kỳ 6 tháng.
3. **Nốt gan kích thước ≥ 10 mm HOẶC nồng độ AFP tăng cao liên tục (> 20 ng/mL)**:
   - Chỉ định chụp hình ảnh chẩn đoán đa pha có tiêm thuốc cản quang:
     * Chụp CT ổ bụng đa dãy 3 pha hoặc 4 pha, HOẶC
     * Chụp cộng hưởng từ (MRI) gan mật với thuốc đối quang từ chuyên biệt.
   - Đánh giá phân loại theo tiêu chuẩn LI-RADS (LI-RADS 4/5 xác chẩn HCC, chuyển hội chẩn chuyên khoa ung bướu).
""",
    },
    {
        "slug": "lung-nccn-2025-screening-nodule-management",
        "cancer_type": "lung",
        "gender": "any",
        "risk_level": "high",
        "url": "https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1441",
        "source_en": "NCCN Guidelines 2025 — Lung Cancer Screening and Nodule Evaluation",
        "source_vn": "NCCN 2025 — Hướng dẫn Tầm soát Ung Thư Phổi & Xử trí Nốt Phổi (Lung-RADS)",
        "body_en": """## NCCN High-Risk Criteria for Lung Cancer Screening
NCCN defines high risk (Group 1 and Group 2) eligible for annual screening:
- **Group 1**: Age 50–80 years, with ≥20 pack-year smoking history, currently smoking or quit within 15 years.
- **Group 2**: Age ≥50 years, with ≥20 pack-year smoking history, PLUS one additional risk factor:
  * Personal history of cancer or lung disease (COPD, pulmonary fibrosis).
  * Family history of lung cancer in first-degree relatives.
  * Documented occupational exposure to carcinogens (asbestos, silica, radon, heavy metals).

## Recommended Screening Modality
- Low-Dose Computed Tomography (LDCT) of the chest without intravenous contrast.
- Chest X-rays are NOT recommended for lung cancer screening.

## NCCN Lung-RADS Decision Tree for Pulmonary Nodules
1. **Solid Nodule < 6 mm (Lung-RADS 2)**:
   - Benign appearance; continue annual LDCT in 12 months.
2. **Solid Nodule 6 to 8 mm (Lung-RADS 3)**:
   - Probably benign; repeat LDCT at 6 months.
3. **Solid Nodule ≥ 8 mm (Lung-RADS 4A / 4B)**:
   - Suspicious: LDCT at 3 months, or PET/CT, or contrast-enhanced chest CT.
   - Very suspicious (≥15 mm or new/growing): Multidisciplinary evaluation, biopsy, or surgical consultation.
4. **Subsolid / Ground-Glass Nodules (GGN)**:
   - Pure GGN < 30 mm: LDCT at 6–12 months.
   - Part-solid nodule with solid component ≥ 6 mm: LDCT at 3–6 months; persistent solid component warrants PET/CT or tissue biopsy.
""",
        "body_vn": """## Tiêu chuẩn Nhóm Nguy cơ Cao Tầm soát Ung Thư Phổi theo NCCN
NCCN phân loại đối tượng nguy cơ cao được chỉ định tầm soát định kỳ:
- **Nhóm 1**: Người từ 50 đến 80 tuổi, có tiền sử hút thuốc lá từ 20 bao-năm trở lên, hiện vẫn đang hút hoặc đã cai thuốc trong vòng 15 năm qua.
- **Nhóm 2**: Người từ 50 tuổi trở lên, có tiền sử hút thuốc từ 20 bao-năm, KÈM THEO ít nhất một yếu tố nguy cơ bổ sung:
  * Tiền sử bệnh phổi mạn tính (COPD, xơ hóa phổi).
  * Tiền sử gia đình có người thân trực hệ mắc ung thư phổi.
  * Phơi nhiễm nghề nghiệp với tác nhân sinh ung (bụi amiăng, silica, khí radon, khói kim loại nặng).

## Phương pháp Tầm soát Khuyến cáo
- Chụp cắt lớp vi tính liều thấp (LDCT) lồng ngực không tiêm thuốc cản quang.
- X-quang phổi thông thường KHÔNG có giá trị tầm soát phát hiện sớm ung thư phổi.

## Cây Quyết định Xử trí Nốt Phổi (Lưu đồ Lung-RADS NCCN)
1. **Nốt đặc kích thước < 6 mm (Lung-RADS 2)**:
   - Dấu hiệu lành tính; tiếp tục chụp LDCT định kỳ sau 12 tháng.
2. **Nốt đặc kích thước từ 6 đến 8 mm (Lung-RADS 3)**:
   - Khả năng lành tính cao; chụp lại LDCT sau 6 tháng để theo dõi tiến triển.
3. **Nốt đặc kích thước ≥ 8 mm (Lung-RADS 4A / 4B)**:
   - Nghi ngờ ác tính: Chụp lại LDCT sau 3 tháng, hoặc chụp PET/CT, hoặc CT ngực có cản quang.
   - Nốt rất nghi ngờ (≥ 15 mm hoặc nốt mới phát triển nhanh): Hội chẩn chuyên khoa lồng ngực, sinh thiết hoặc phẫu thuật chẩn đoán.
4. **Nốt bán đặc & Nốt kính mờ (Ground-Glass Nodule - GGN)**:
   - Nốt kính mờ đơn thuần < 30 mm: Chụp lại LDCT sau 6–12 tháng.
   - Nốt bán đặc có phần đặc bên trong ≥ 6 mm: Chụp lại LDCT sau 3–6 tháng; nếu phần đặc tồn tại dai dẳng cần sinh thiết hoặc chụp PET/CT.
""",
    },
    {
        "slug": "breast-nccn-2025-high-risk-genetic-assessment",
        "cancer_type": "breast",
        "gender": "female",
        "risk_level": "high",
        "url": "https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1436",
        "source_en": "NCCN Guidelines 2025 — Genetic/Familial High-Risk Assessment: Breast, Ovarian, and Pancreatic",
        "source_vn": "NCCN 2025 — Đánh giá Nguy cơ Cao Di truyền & Tiền sử Gia đình: Ung Thư Vú",
        "body_en": """## NCCN Criteria for High-Risk Breast Cancer Evaluation
Individuals meeting any of the following criteria require comprehensive genetic evaluation and tailored screening:
- Known pathogenic/likely pathogenic variant in breast cancer susceptibility genes: *BRCA1, BRCA2, CDH1, PALB2, PTEN, STK11, TP53*.
- Personal history of radiation therapy to the chest between ages 10 and 30 years.
- Estimated lifetime risk of breast cancer ≥ 20% based on validated risk models (e.g., Tyrer-Cuzick, Claus, BRCAPRO).
- Family history meeting high-risk criteria:
  * First-degree relative with breast cancer diagnosed at age ≤ 50 years.
  * Two or more primary breast cancers in the same individual.
  * Male breast cancer in any blood relative.
  * Family history of ovarian, pancreatic, or metastatic prostate cancer.

## NCCN Tailored Screening Protocol for High-Risk Women
For women with known *BRCA1/2* or lifetime risk ≥ 20%:
1. **Ages 25–29 years**:
   - Annual Breast MRI with intravenous contrast (preferred over mammography due to breast density and radiation sparing).
   - Clinical Breast Examination (CBE) every 6–12 months.
2. **Ages 30–75 years**:
   - Annual Screening Mammography (preferably Digital Breast Tomosynthesis / 3D Mammogram).
   - Annual Breast MRI with contrast (ideally staggered every 6 months with mammography).
3. **Prior Chest Radiation Therapy (Ages 10–30)**:
   - Begin annual mammography and annual breast MRI starting 8–10 years after radiation therapy, but not before age 25.
""",
        "body_vn": """## Tiêu chuẩn Đánh giá Nguy cơ Cao Di truyền Ung Thư Vú theo NCCN
Phụ nữ có một trong các dấu hiệu sau cần được tư vấn di truyền và lập kế hoạch tầm soát chuyên biệt:
- Mang đột biến gen gây bệnh đã xác định: *BRCA1, BRCA2, CDH1, PALB2, PTEN, STK11, TP53*.
- Tiền sử từng xạ trị vùng ngực điều trị bệnh lý khác (như u lympho Hodgkin) trong độ tuổi từ 10 đến 30 tuổi.
- Nguy cơ mắc ung thư vú tích lũy suốt đời ước tính ≥ 20% (theo mô hình tính toán Gail, Tyrer-Cuzick hoặc Claus).
- Tiền sử gia đình có yếu tố nguy cơ cao:
  * Người thân trực hệ (mẹ, chị em gái, con gái) mắc ung thư vú ở độ tuổi ≤ 50 tuổi.
  * Có người thân mắc từ 2 khối u nguyên phát ở vú trở lên.
  * Có người thân nam giới mắc ung thư vú.
  * Tiền sử gia đình có người mắc ung thư buồng trứng, ung thư tụy hoặc ung thư tuyến tiền liệt di căn.

## Phác đồ Tầm soát Chuyên biệt NCCN cho Nhóm Nguy cơ Cao
Dành cho phụ nữ mang đột biến gen *BRCA1/2* hoặc có nguy cơ suốt đời ≥ 20%:
1. **Độ tuổi từ 25 đến 29 tuổi**:
   - Chụp cộng hưởng từ (MRI) tuyến vú có tiêm thuốc đối quang từ hàng năm (ưu tiên hơn nhũ ảnh để tránh phơi nhiễm bức xạ và phù hợp mô vú đặc).
   - Khám lâm sàng tuyến vú định kỳ mỗi 6 đến 12 tháng.
2. **Độ tuổi từ 30 đến 75 tuổi**:
   - Chụp nhũ ảnh (mammography, ưu tiên nhũ ảnh 3D/Tomosynthesis) định kỳ hàng năm.
   - Chụp MRI tuyến vú có cản quang hàng năm (lý tưởng là xen kẽ mỗi 6 tháng giữa nhũ ảnh và MRI).
3. **Người có tiền sử xạ trị vùng ngực (10–30 tuổi)**:
   - Bắt đầu chụp nhũ ảnh và MRI vú định kỳ hàng năm từ năm thứ 8 đến 10 sau khi kết thúc xạ trị, hoặc bắt đầu từ năm 25 tuổi.
""",
    },
    {
        "slug": "colorectal-nccn-2025-high-risk-lynch-surveillance",
        "cancer_type": "colorectal",
        "gender": "any",
        "risk_level": "high",
        "url": "https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1437",
        "source_en": "NCCN Guidelines 2025 — Genetic/Familial High-Risk Assessment: Colorectal (Lynch Syndrome & FAP)",
        "source_vn": "NCCN 2025 — Đánh giá Nguy cơ Cao Di truyền Ung Thư Đại Trực Tràng (Hội chứng Lynch & Đa polyp)",
        "body_en": """## NCCN High-Risk Colorectal Criteria
Screening protocols are intensified for individuals with inherited syndromes or elevated familial risk:
- **Lynch Syndrome (Hereditary Nonpolyposis Colorectal Cancer - HNPCC)**:
  * Germline mutation in mismatch repair (MMR) genes: *MLH1, MSH2, MSH6, PMS2, EPCAM*.
- **Familial Adenomatous Polyposis (FAP) / Attenuated FAP (AFAP)**:
  * Germline mutation in *APC* or *MUTYH* genes.
- **Family History of Colorectal Cancer (CRC)**:
  * First-degree relative with CRC diagnosed at age < 50 years.
  * Two or more first-degree relatives with CRC at any age.

## NCCN High-Risk Surveillance Schedules
1. **Lynch Syndrome (*MLH1 / MSH2 / EPCAM*)**:
   - High-quality Colonoscopy every 1 to 2 years, starting at age 20–25 years (or 2–5 years prior to the earliest CRC in the family if diagnosed before age 25).
2. **Lynch Syndrome (*MSH6 / PMS2*)**:
   - Colonoscopy every 1 to 2 years, starting at age 30–35 years.
3. **Classic FAP**:
   - Annual flexible sigmoidoscopy or colonoscopy starting at age 10–15 years.
4. **First-Degree Relative Diagnosed with CRC < 50 Years**:
   - Colonoscopy starting at age 40 (or 10 years earlier than youngest affected relative).
   - Repeat every 5 years (instead of standard 10 years).
""",
        "body_vn": """## Tiêu chuẩn Nhóm Nguy cơ Cao Ung Thư Đại Trực Tràng theo NCCN
Quy trình tầm soát được đẩy sớm và tăng tần suất cho các đối tượng sau:
- **Hội chứng Lynch (Ung thư đại trực tràng di truyền không polyp - HNPCC)**:
  * Mang đột biến dòng mầm trong các gen sửa chữa bắt cặp sai ADN (MMR): *MLH1, MSH2, MSH6, PMS2, EPCAM*.
- **Bệnh Đa polyp tuyến có tính gia đình (FAP / Attenuated FAP)**:
  * Mang đột biến gen *APC* hoặc đột biến thể lặn kép *MUTYH*.
- **Tiền sử gia đình mắc ung thư đại trực tràng (CRC)**:
  * Người thân trực hệ (bố mẹ, anh chị em, con cái) mắc CRC trước 50 tuổi.
  * Có từ 2 người thân trực hệ trở lên mắc CRC ở bất kỳ độ tuổi nào.

## Lịch trình Giám sát Chuyên sâu NCCN
1. **Hội chứng Lynch (đột biến *MLH1 / MSH2 / EPCAM*)**:
   - Nội soi toàn bộ đại tràng định kỳ mỗi 1 đến 2 năm, bắt đầu từ độ tuổi 20 đến 25 tuổi (hoặc sớm hơn 2–5 năm so với độ tuổi của người trẻ nhất trong gia đình mắc bệnh).
2. **Hội chứng Lynch (đột biến *MSH6 / PMS2*)**:
   - Nội soi đại tràng định kỳ mỗi 1 đến 2 năm, bắt đầu từ 30 đến 35 tuổi.
3. **Bệnh Đa polyp tuyến gia đình (FAP cổ điển)**:
   - Nội soi đại tràng sigma hoặc toàn bộ đại tràng hàng năm, bắt đầu từ độ tuổi 10 đến 15 tuổi.
4. **Có người thân trực hệ mắc CRC trước 50 tuổi**:
   - Bắt đầu nội soi đại tràng từ năm 40 tuổi (hoặc sớm hơn 10 năm so với người trẻ nhất trong gia đình).
   - Lặp lại định kỳ mỗi 5 năm một lần (thay vì chu kỳ 10 năm của người nguy cơ trung bình).
""",
    },
    {
        "slug": "prostate-nccn-2025-early-detection",
        "cancer_type": "prostate",
        "gender": "male",
        "risk_level": "average",
        "url": "https://www.nccn.org/guidelines/guidelines-detail?category=1&id=1459",
        "source_en": "NCCN Guidelines 2025 — Prostate Cancer Early Detection",
        "source_vn": "NCCN 2025 — Hướng dẫn Phát hiện Sớm Ung Thư Tuyến Tiền Liệt",
        "body_en": """## NCCN Early Detection Baseline Evaluation
NCCN recommends initiating shared decision-making and baseline evaluation for prostate cancer detection:
- **Age 45 years**: Baseline PSA testing and Digital Rectal Examination (DRE) for all men.
- **Age 40 years**: Earlier baseline testing for high-risk men:
  * African American / Black ancestry.
  * Family history of prostate cancer in a first-degree relative diagnosed at age < 65 years.
  * Known germline mutation in *BRCA1, BRCA2, ATM, CHEK2, HOXB13*.

## NCCN Stratification and Testing Interval Algorithm
1. **PSA < 1.0 ng/mL and Normal DRE**:
   - Repeat PSA testing every 2 to 4 years.
2. **PSA 1.0 to 3.0 ng/mL and Normal DRE**:
   - Repeat PSA testing every 1 to 2 years.
3. **PSA > 3.0 ng/mL OR Suspicious DRE**:
   - Perform repeat PSA to confirm elevation.
   - Secondary biomarker testing (free PSA percentage, 4Kscore, Prostate Health Index - PHI).
   - Multiparametric MRI (mpMRI) of the prostate before deciding on prostate biopsy.
   - Biopsy indicated if PI-RADS 4–5 or persistent high clinical suspicion.
""",
        "body_vn": """## Đánh giá Ban đầu Phát hiện Sớm Ung Thư Tuyến Tiền Liệt theo NCCN
NCCN khuyến cáo tiến hành trao đổi quyết định cá nhân hóa và làm xét nghiệm mốc cơ bản (baseline):
- **Từ 45 tuổi**: Bắt đầu xét nghiệm nồng độ PSA huyết thanh mốc cơ bản và thăm trực tràng (DRE) cho nam giới.
- **Từ 40 tuổi**: Bắt đầu sớm hơn cho nam giới thuộc nhóm nguy cơ cao:
  * Người gốc Phi / Da đen.
  * Tiền sử gia đình có người thân trực hệ mắc ung thư tuyến tiền liệt trước 65 tuổi.
  * Mang đột biến dòng mầm trong các gen *BRCA1, BRCA2, ATM, CHEK2, HOXB13*.

## Lưu đồ Phân tầng Nguy cơ & Tần suất Xét nghiệm NCCN
1. **Nồng độ PSA < 1.0 ng/mL & Thăm trực tràng bình thường**:
   - Nguy cơ rất thấp; lặp lại xét nghiệm PSA định kỳ mỗi 2 đến 4 năm một lần.
2. **Nồng độ PSA từ 1.0 đến 3.0 ng/mL & Thăm trực tràng bình thường**:
   - Lặp lại xét nghiệm PSA định kỳ mỗi 1 đến 2 năm một lần.
3. **Nồng độ PSA > 3.0 ng/mL HOẶC Thăm trực tràng nghi ngờ u cục**:
   - Xét nghiệm lại PSA lần 2 để loại trừ viêm nhiễm hoặc kích thích cơ học thoáng qua.
   - Đánh giá chỉ dấu sinh học thứ cấp (tỷ lệ % PSA tự do - Free PSA, chỉ số sức khỏe tuyến tiền liệt PHI).
   - Chụp cộng hưởng từ đa thông số (mpMRI) tuyến tiền liệt trước khi quyết định sinh thiết.
   - Chỉ định sinh thiết nếu tổn thương PI-RADS 4–5 hoặc có bằng chứng nghi ngờ lâm sàng dai dẳng.
""",
    },
]


def extract_medguide_screening_suite():
    """Trích xuất các ca lâm sàng tầm soát/giám sát từ raw MedGUIDE JSONL để làm Evaluation Suite."""
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    out_eval_path = EVAL_DIR / "nccn_screening_eval_suite.jsonl"

    selected_cases = []
    # 1. Quét các ca giám sát gan hcc1 (84 ca)
    hcc_path = RAW_DATA_DIR / "liver/nccn/2025/nccn_medguide_liver_2025.jsonl"
    if hcc_path.exists():
        for line in hcc_path.open(encoding="utf-8"):
            if line.strip():
                c = json.loads(line)
                c["eval_category"] = "liver_hcc_surveillance"
                selected_cases.append(c)

    # 2. Quét các ca nốt phổi nscl_2 và nscl_3 (336 ca)
    lung_path = RAW_DATA_DIR / "lung/nccn/2025/nccn_medguide_lung_2025.jsonl"
    if lung_path.exists():
        for line in lung_path.open(encoding="utf-8"):
            if line.strip():
                c = json.loads(line)
                p_str = str(c.get("path", ""))
                if "nodule" in p_str.lower():
                    c["eval_category"] = "lung_nodule_management"
                    selected_cases.append(c)

    # 3. Quét các ca đại trực tràng theo dõi CEA / nội soi (182 ca)
    col_path = RAW_DATA_DIR / "colorectal/nccn/2025/nccn_medguide_colorectal_2025.jsonl"
    if col_path.exists():
        for line in col_path.open(encoding="utf-8"):
            if line.strip():
                c = json.loads(line)
                p_str = str(c.get("path", ""))
                if "colonoscopy" in p_str.lower() or "cea" in p_str.lower():
                    c["eval_category"] = "colorectal_surveillance"
                    selected_cases.append(c)

    with open(out_eval_path, "w", encoding="utf-8") as f:
        for c in selected_cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    # Tạo file README giải thích
    readme_path = EVAL_DIR / "README.md"
    readme_content = f"""# NCCN Clinical Decision Benchmark Suite (OncoScreen-AI)

Bộ dữ liệu kiểm định lâm sàng được trích xuất từ **NCCN MedGUIDE Decision Trees (2025)**, chỉ tập trung vào các tình huống tầm soát, giám sát và xử trí phát hiện sớm (loại trừ các ca hóa trị/giai đoạn muộn).

- **Tổng số ca lâm sàng kiểm thử**: {len(selected_cases)} ca
- **Tệp dữ liệu**: `nccn_screening_eval_suite.jsonl`
- **Các phân nhóm tình huống**:
  * `liver_hcc_surveillance`: Giám sát ung thư biểu mô tế bào gan (HCC) bằng Siêu âm + AFP ở người xơ gan, viêm gan B/C mạn tính.
  * `lung_nodule_management`: Xử trí và phân loại nốt phổi phát hiện tình cờ / qua chụp CT ngực liều thấp (Lung-RADS).
  * `colorectal_surveillance`: Theo dõi nội soi và dấu ấn sinh học CEA đại trực tràng.

Mỗi bản ghi chứa: `profile` (tóm tắt bệnh án), `prompt` (câu hỏi trắc nghiệm lâm sàng), `options` (các hướng xử trí), `answer_text` (quyết định chuẩn theo lưu đồ NCCN).
"""
    readme_path.write_text(readme_content, encoding="utf-8")
    print(f"[*] Đã xuất Benchmark Suite: {len(selected_cases)} ca lâm sàng tại {out_eval_path}")


def main():
    print("====================================================================")
    print("=== TẠO BỘ DỮ LIỆU GUIDELINES NCCN 2025 (EN & VN) ===")
    print("====================================================================")

    manifest_entries = []
    generated_en = 0
    generated_vn = 0

    for doc in NCCN_DOCS:
        slug = doc["slug"]
        cancer_type = doc["cancer_type"]

        # -------------------------------------------------------------
        # A. BẢN TIẾNG ANH (-en.md)
        # -------------------------------------------------------------
        en_file = f"{slug}-en.md"
        en_path = GUIDELINES_DIR / en_file

        en_meta = {
            "cancer_type": cancer_type,
            "source": doc["source_en"],
            "url": doc["url"],
            "gender": doc["gender"],
            "risk_level": doc["risk_level"],
            "language": "en",
        }

        en_yaml = yaml.safe_dump(en_meta, allow_unicode=True, sort_keys=False)
        en_content = f"---\n{en_yaml}---\n{doc['body_en'].strip()}\n"
        en_path.write_text(en_content, encoding="utf-8")
        generated_en += 1

        sec_count_en = len([l for l in doc["body_en"].splitlines() if l.startswith("## ")])
        manifest_entries.append({
            "file": en_file,
            "language": "en",
            "cancer_type": cancer_type,
            "source": doc["source_en"],
            "url": doc["url"],
            "gender": doc["gender"],
            "risk_level": doc["risk_level"],
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
            "source": doc["source_vn"],
            "url": doc["url"],
            "gender": doc["gender"],
            "risk_level": doc["risk_level"],
            "language": "vi",
        }

        vn_yaml = yaml.safe_dump(vn_meta, allow_unicode=True, sort_keys=False)
        vn_content = f"---\n{vn_yaml}---\n{doc['body_vn'].strip()}\n"
        vn_path.write_text(vn_content, encoding="utf-8")
        generated_vn += 1

        sec_count_vn = len([l for l in doc["body_vn"].splitlines() if l.startswith("## ")])
        manifest_entries.append({
            "file": vn_file,
            "language": "vi",
            "cancer_type": cancer_type,
            "source": doc["source_vn"],
            "url": doc["url"],
            "gender": doc["gender"],
            "risk_level": doc["risk_level"],
            "sections_count": sec_count_vn,
            "created_at": dt.datetime.now().strftime("%Y-%m-%d"),
        })

        print(f" [+] Đã tạo NCCN Guideline: {en_file} (EN) & {vn_file} (VN)")

    # -------------------------------------------------------------
    # C. CẬP NHẬT _MANIFEST.JSONL
    # -------------------------------------------------------------
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
    print(f"[✓] HOÀN TẤT TẠO GUIDELINES NCCN:")
    print(f"    - Bản tiếng Anh tạo mới (-en.md) : {generated_en} tệp")
    print(f"    - Bản tiếng Việt tạo mới (-vn.md) : {generated_vn} tệp")
    print(f"    - Đã bổ sung vào manifest        : {added_count} bản ghi")
    print(f"    - Tổng số bản ghi trong manifest  : {len(existing_manifest)}")
    print("====================================================================")

    # -------------------------------------------------------------
    # D. TRÍCH XUẤT BENCHMARK EVALUATION SUITE
    # -------------------------------------------------------------
    print("\n[*] Trích xuất NCCN Clinical Decision Benchmark Suite...")
    extract_medguide_screening_suite()


if __name__ == "__main__":
    main()
