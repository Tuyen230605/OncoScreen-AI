/**
 * Dữ liệu tĩnh cho chế độ mock (NEXT_PUBLIC_USE_MOCK_API=true).
 * Mirror của ai_core/data (questionnaire.json, services.json, screening_rules.json, red_flags.json) và
 * ai_core/guardrails/disclaimer.py — giữ đồng bộ khi các file đó thay đổi.
 */
import type {
  CancerType,
  EducationContent,
  Gender,
  Questionnaire,
  RedFlagSeverity,
  ServiceOut,
  Source,
} from "@/types/api";

export const DISCLAIMER =
  "Thông tin trong hệ thống này chỉ mang tính giáo dục và tham khảo về tầm soát ung thư, KHÔNG phải chẩn đoán y khoa và không thay thế ý kiến của bác sĩ. Kế hoạch tầm soát cá nhân chỉ có hiệu lực khi đã được bác sĩ xem xét và phê duyệt. Nếu bạn có triệu chứng bất thường, hãy đến cơ sở y tế để được khám trực tiếp.";

export const COPILOT_DISCLAIMER =
  "Công cụ hỗ trợ ra quyết định lâm sàng: tóm tắt hồ sơ và đối chiếu guideline có trích dẫn. AI không chẩn đoán và không diễn giải kết quả cận lâm sàng; bác sĩ chịu trách nhiệm chẩn đoán, chỉ định và phê duyệt kế hoạch trước khi gửi bệnh nhân.";

export const RED_FLAG_MESSAGE =
  "Bạn có dấu hiệu cần được bác sĩ khám trực tiếp sớm. Hệ thống tạm dừng tư vấn tầm soát định kỳ để bạn ưu tiên đi khám. Điều này không có nghĩa là bạn mắc bệnh, chỉ là cần được đánh giá kỹ hơn.";

export const MOCK_PASSWORD = "123456";
export const MOCK_MODEL = "mock-template";
export const MAX_CONSULT_TURNS = 40;

export const LABEL_VI: Record<CancerType, string> = {
  breast: "ung thư vú",
  cervical: "ung thư cổ tử cung",
  colorectal: "ung thư đại trực tràng",
  liver: "ung thư gan",
  lung: "ung thư phổi",
  prostate: "ung thư tuyến tiền liệt",
  other: "ung thư khác",
};

// ---------------------------------------------------------------- dịch vụ (services.json)
export const SERVICES: ServiceOut[] = [
  {
    code: "general_screening",
    name: "Khám tư vấn tầm soát ung thư",
    cancer_types: ["other"],
    description: "Bác sĩ đánh giá yếu tố nguy cơ và chỉ định các xét nghiệm tầm soát phù hợp.",
  },
  {
    code: "breast_screening",
    name: "Tầm soát ung thư vú",
    cancer_types: ["breast"],
    description: "Khám vú, chụp nhũ ảnh/siêu âm theo chỉ định của bác sĩ.",
  },
  {
    code: "cervical_screening",
    name: "Tầm soát ung thư cổ tử cung",
    cancer_types: ["cervical"],
    description: "Khám phụ khoa, xét nghiệm HPV/Pap theo chỉ định.",
  },
  {
    code: "colorectal_screening",
    name: "Tầm soát ung thư đại trực tràng",
    cancer_types: ["colorectal"],
    description: "Tư vấn xét nghiệm FIT hoặc nội soi đại tràng.",
  },
  {
    code: "lung_screening",
    name: "Tầm soát ung thư phổi",
    cancer_types: ["lung"],
    description: "Đánh giá tiền sử hút thuốc và chỉ định CT phổi liều thấp.",
  },
  {
    code: "liver_screening",
    name: "Giám sát ung thư gan",
    cancer_types: ["liver"],
    description: "Khám gan mật, siêu âm gan và AFP cho nhóm nguy cơ cao.",
  },
  {
    code: "prostate_consult",
    name: "Tư vấn tầm soát ung thư tuyến tiền liệt",
    cancer_types: ["prostate"],
    description: "Trao đổi lợi ích/nguy cơ của xét nghiệm PSA.",
  },
  {
    code: "oncology_followup",
    name: "Khám chuyên khoa Ung bướu",
    cancer_types: [],
    description: "Dành cho người đã từng được chẩn đoán ung thư cần theo dõi.",
  },
  {
    code: "oncology_priority",
    name: "Khám ưu tiên: có dấu hiệu cần đánh giá sớm",
    cancer_types: [],
    description: "Lịch ưu tiên khi có triệu chứng cảnh báo (khối u, chảy máu bất thường, sụt cân…).",
  },
];

// ---------------------------------------------------------------- bảng hỏi nhanh (questionnaire.json)
export const NAVIGATOR_QUESTIONNAIRE: Questionnaire = {
  version: "0.2",
  questions: [
    { id: "age", text: "Bạn bao nhiêu tuổi?", type: "number", options: null, required: true, depends_on: null },
    {
      id: "gender",
      text: "Giới tính của bạn?",
      type: "single_choice",
      options: ["Nữ", "Nam", "Khác"],
      required: true,
      depends_on: null,
    },
    {
      id: "family_history",
      text: "Trong gia đình (bố, mẹ, anh chị em ruột, con) có ai từng mắc ung thư không?",
      type: "multi_choice",
      options: [
        "Không",
        "Ung thư vú",
        "Ung thư cổ tử cung",
        "Ung thư đại trực tràng",
        "Ung thư gan",
        "Ung thư phổi",
        "Ung thư tuyến tiền liệt",
        "Khác",
      ],
      required: true,
      depends_on: null,
    },
    {
      id: "personal_cancer_history",
      text: "Bản thân bạn đã từng được chẩn đoán ung thư chưa?",
      type: "boolean",
      options: null,
      required: true,
      depends_on: null,
    },
    {
      id: "smoking",
      text: "Bạn đang hút thuốc hoặc đã bỏ thuốc trong vòng 15 năm gần đây?",
      type: "boolean",
      options: null,
      required: true,
      depends_on: null,
    },
    {
      id: "pack_years",
      text: "Ước tính số gói-năm (số gói/ngày × số năm hút)?",
      type: "number",
      options: null,
      required: true,
      depends_on: "smoking=true",
    },
    {
      id: "hbv_hcv",
      text: "Bạn có đang mang viêm gan B hoặc C mạn tính không?",
      type: "boolean",
      options: null,
      required: true,
      depends_on: null,
    },
    {
      id: "cirrhosis",
      text: "Bác sĩ đã từng nói bạn bị xơ gan chưa?",
      type: "boolean",
      options: null,
      required: false,
      depends_on: null,
    },
    {
      id: "hpv_vaccine",
      text: "Bạn đã tiêm vắc-xin HPV chưa?",
      type: "boolean",
      options: null,
      required: false,
      depends_on: "gender=Nữ",
    },
    {
      id: "symptom_lump",
      text: "Gần đây bạn có sờ thấy khối u hoặc cục bất thường ở vú, cổ, bụng hay nơi nào khác không?",
      type: "boolean",
      options: null,
      required: true,
      depends_on: null,
    },
    {
      id: "symptom_bleeding",
      text: "Bạn có bị chảy máu bất thường (đi ngoài ra máu, ho ra máu, ra máu âm đạo ngoài kỳ kinh) không?",
      type: "boolean",
      options: null,
      required: true,
      depends_on: null,
    },
    {
      id: "symptom_weight_loss",
      text: "Bạn có sụt cân nhanh (>5% cân nặng trong 6 tháng) mà không rõ nguyên nhân không?",
      type: "boolean",
      options: null,
      required: true,
      depends_on: null,
    },
    {
      id: "symptom_persistent_pain",
      text: "Bạn có cơn đau kéo dài trên 3 tuần không giải thích được không?",
      type: "boolean",
      options: null,
      required: true,
      depends_on: null,
    },
    {
      id: "other_symptoms",
      text: "Bạn có triệu chứng nào khác muốn chia sẻ không? (tuỳ chọn)",
      type: "text",
      options: null,
      required: false,
      depends_on: null,
    },
  ],
};

// ---------------------------------------------------------------- nguồn guideline
export const GUIDELINE_SOURCES: Record<string, Source> = {
  breast_uspstf_2024: {
    doc_id: "breast_uspstf_2024",
    title: "USPSTF 2024 — Tầm soát ung thư vú",
    section: "Khuyến nghị",
    excerpt: "Khuyến nghị chụp nhũ ảnh 2 năm một lần cho phụ nữ 40–74 tuổi có nguy cơ trung bình.",
    url: "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/breast-cancer-screening",
  },
  cervical_uspstf_2018: {
    doc_id: "cervical_uspstf_2018",
    title: "USPSTF 2018 — Tầm soát ung thư cổ tử cung",
    section: "Khuyến nghị",
    excerpt:
      "Phụ nữ 21–29 tuổi: xét nghiệm tế bào học mỗi 3 năm. Phụ nữ 30–65 tuổi: xét nghiệm HPV nguy cơ cao mỗi 5 năm hoặc tế bào học mỗi 3 năm.",
    url: "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/cervical-cancer-screening",
  },
  colorectal_uspstf_2021: {
    doc_id: "colorectal_uspstf_2021",
    title: "USPSTF 2021 — Tầm soát ung thư đại trực tràng",
    section: "Khuyến nghị",
    excerpt: "Khuyến nghị tầm soát ung thư đại trực tràng cho mọi người trưởng thành 45–75 tuổi.",
    url: "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/colorectal-cancer-screening",
  },
  lung_uspstf_2021: {
    doc_id: "lung_uspstf_2021",
    title: "USPSTF 2021 — Tầm soát ung thư phổi",
    section: "Khuyến nghị",
    excerpt:
      "Chụp CT phổi liều thấp hằng năm cho người 50–80 tuổi, hút thuốc từ 20 gói-năm và đang hút hoặc bỏ thuốc chưa quá 15 năm.",
    url: "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/lung-cancer-screening",
  },
  prostate_uspstf_2018: {
    doc_id: "prostate_uspstf_2018",
    title: "USPSTF 2018 — Tầm soát ung thư tuyến tiền liệt",
    section: "Khuyến nghị",
    excerpt:
      "Nam giới 55–69 tuổi: quyết định xét nghiệm PSA định kỳ là quyết định cá nhân, sau khi trao đổi lợi ích và nguy cơ với bác sĩ.",
    url: "https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/prostate-cancer-screening",
  },
  liver_aasld_2023: {
    doc_id: "liver_aasld_2023",
    title: "AASLD 2023 — Hướng dẫn thực hành dự phòng, chẩn đoán và điều trị ung thư biểu mô tế bào gan",
    section: "Khuyến nghị giám sát",
    excerpt: "Người nguy cơ cao (xơ gan, viêm gan B mạn) nên được giám sát bằng siêu âm gan kèm AFP mỗi 6 tháng.",
    url: "https://doi.org/10.1097/HEP.0000000000000466",
  },
  other_who_screening_guide_2022: {
    doc_id: "other_who_screening_guide_2022",
    title: "WHO Europe 2022 — Hướng dẫn ngắn về chương trình sàng lọc ung thư",
    section: "Nguyên tắc chung",
    excerpt:
      "Sàng lọc chỉ mang lại lợi ích khi được thực hiện đúng đối tượng, đúng tần suất và có quy trình theo dõi kết quả bất thường.",
    url: "https://www.who.int/publications/i/item/9789289057561",
  },
};

// ---------------------------------------------------------------- luật tầm soát (screening_rules.json)
export type RuleRequirement = "pack_years>=20" | "cirrhosis" | "hepatitis_without_cirrhosis";

export interface ScreeningRule {
  id: string;
  cancer_type: CancerType;
  doc_id: string;
  gender: Gender | "any";
  min_age: number;
  max_age: number | null;
  requires: RuleRequirement[];
  method: string;
  start_age: number | null;
  interval_months: number | null;
  applies_because: string;
  family_note: string | null;
}

export const SCREENING_RULES: ScreeningRule[] = [
  {
    id: "breast_40_74",
    cancer_type: "breast",
    doc_id: "breast_uspstf_2024",
    gender: "female",
    min_age: 40,
    max_age: 74,
    requires: [],
    method: "Chụp nhũ ảnh (mammography)",
    start_age: 40,
    interval_months: 24,
    applies_because: "Phụ nữ 40–74 tuổi",
    family_note:
      "Có người thân mắc ung thư vú: guideline nguy cơ trung bình có thể không đủ; bác sĩ cần đánh giá kế hoạch riêng.",
  },
  {
    id: "cervical_21_29",
    cancer_type: "cervical",
    doc_id: "cervical_uspstf_2018",
    gender: "female",
    min_age: 21,
    max_age: 29,
    requires: [],
    method: "Xét nghiệm tế bào học cổ tử cung (Pap)",
    start_age: 21,
    interval_months: 36,
    applies_because: "Phụ nữ 21–29 tuổi",
    family_note: null,
  },
  {
    id: "cervical_30_65",
    cancer_type: "cervical",
    doc_id: "cervical_uspstf_2018",
    gender: "female",
    min_age: 30,
    max_age: 65,
    requires: [],
    method: "Xét nghiệm HPV nguy cơ cao (hoặc Pap mỗi 3 năm)",
    start_age: 30,
    interval_months: 60,
    applies_because: "Phụ nữ 30–65 tuổi",
    family_note: null,
  },
  {
    id: "colorectal_45_75",
    cancer_type: "colorectal",
    doc_id: "colorectal_uspstf_2021",
    gender: "any",
    min_age: 45,
    max_age: 75,
    requires: [],
    method: "Xét nghiệm FIT (hoặc nội soi đại tràng mỗi 10 năm)",
    start_age: 45,
    interval_months: 12,
    applies_because: "Người 45–75 tuổi",
    family_note:
      "Có người thân mắc ung thư đại trực tràng: thường cần bắt đầu sớm hơn và chọn phương pháp riêng; bác sĩ quyết định.",
  },
  {
    id: "lung_50_80_20py",
    cancer_type: "lung",
    doc_id: "lung_uspstf_2021",
    gender: "any",
    min_age: 50,
    max_age: 80,
    requires: ["pack_years>=20"],
    method: "Chụp CT phổi liều thấp (LDCT)",
    start_age: 50,
    interval_months: 12,
    applies_because: "Người 50–80 tuổi, hút thuốc từ 20 gói-năm (còn hút hoặc bỏ dưới 15 năm)",
    family_note: null,
  },
  {
    id: "prostate_55_69_sdm",
    cancer_type: "prostate",
    doc_id: "prostate_uspstf_2018",
    gender: "male",
    min_age: 55,
    max_age: 69,
    requires: [],
    method: "Trao đổi với bác sĩ về xét nghiệm PSA (quyết định cá nhân)",
    start_age: 55,
    interval_months: null,
    applies_because: "Nam giới 55–69 tuổi",
    family_note: "Có người thân mắc ung thư tuyến tiền liệt: nguy cơ cao hơn, cần bác sĩ tư vấn riêng.",
  },
  {
    id: "liver_high_risk_6m",
    cancer_type: "liver",
    doc_id: "liver_aasld_2023",
    gender: "any",
    min_age: 18,
    max_age: null,
    requires: ["cirrhosis"],
    method: "Siêu âm gan kèm xét nghiệm AFP",
    start_age: null,
    interval_months: 6,
    applies_because: "Người xơ gan (nhóm nguy cơ cao)",
    family_note: "Có người thân mắc ung thư gan: là yếu tố nguy cơ bổ sung khi bác sĩ đánh giá.",
  },
  {
    id: "liver_hepatitis_specialist",
    cancer_type: "liver",
    doc_id: "liver_aasld_2023",
    gender: "any",
    min_age: 18,
    max_age: null,
    requires: ["hepatitis_without_cirrhosis"],
    method: "Trao đổi với bác sĩ chuyên khoa gan mật về việc giám sát ung thư gan",
    start_age: null,
    interval_months: null,
    applies_because: "Người viêm gan B/C mạn chưa ghi nhận xơ gan: có cần giám sát và chu kỳ bao lâu do bác sĩ xác định",
    family_note: "Có người thân mắc ung thư gan: là yếu tố nguy cơ bổ sung khi bác sĩ đánh giá.",
  },
];

// ---------------------------------------------------------------- red-flag (red_flags.json, mẫu so khớp trên chữ đã bỏ dấu)
export interface RedFlagDef {
  code: string;
  symptom: string;
  severity: RedFlagSeverity;
  advice: string;
  patterns: RegExp[];
}

export const RED_FLAG_DEFS: RedFlagDef[] = [
  {
    code: "symptom_lump",
    symptom: "Sờ thấy khối u / cục bất thường",
    severity: "urgent",
    advice: "Hãy đến cơ sở y tế chuyên khoa để được khám và đánh giá trong vài ngày tới.",
    patterns: [
      /so thay (mot |1 )?(khoi|cuc|u|hach)/,
      /noi (cuc|hach|u)\b/,
      /(co|thay|phat hien) (mot |1 )?(khoi u|cuc u|cuc cung|khoi cung|cuc la|khoi la)/,
      /\bu cuc\b/,
    ],
  },
  {
    code: "symptom_bleeding",
    symptom: "Chảy máu bất thường",
    severity: "urgent",
    advice: "Chảy máu bất thường cần được bác sĩ thăm khám sớm. Đừng trì hoãn.",
    patterns: [
      /(di ngoai|di cau|di tieu|tieu) ra mau/,
      /phan (co |lan )?mau/,
      /ho ra mau/,
      /\bra mau\b/,
      /chay mau bat thuong/,
      /num vu (tiet|chay) (dich|mau)/,
    ],
  },
  {
    code: "symptom_weight_loss",
    symptom: "Sụt cân nhanh không rõ nguyên nhân",
    severity: "soon",
    advice: "Hãy đặt lịch khám tổng quát trong 1–2 tuần tới để tìm nguyên nhân.",
    patterns: [/sut (\d+ ?)?(kg|can|ky)/, /gay sut/],
  },
  {
    code: "symptom_persistent_pain",
    symptom: "Đau kéo dài trên 3 tuần",
    severity: "soon",
    advice: "Đau kéo dài cần được đánh giá bởi bác sĩ; hãy đi khám trong vài tuần tới.",
    patterns: [/dau (keo dai|lien tuc|mai khong (het|khoi)|hoai khong)/],
  },
  {
    code: "symptom_bowel_change",
    symptom: "Thay đổi thói quen đại tiện kéo dài",
    severity: "soon",
    advice: "Thay đổi thói quen đại tiện kéo dài cần được bác sĩ tiêu hoá đánh giá trong vài tuần tới.",
    patterns: [/(thay doi|roi loan) (thoi quen )?(di ngoai|dai tien|di cau)/, /tao bon xen (ke )?(tieu chay|di long)/],
  },
  {
    code: "symptom_jaundice",
    symptom: "Vàng da, vàng mắt",
    severity: "soon",
    advice: "Vàng da hoặc vàng mắt cần được khám sớm để tìm nguyên nhân.",
    patterns: [/vang (da|mat)\b/],
  },
];

// ---------------------------------------------------------------- câu hỏi kiến thức (trả lời có nguồn)
export interface FaqEntry {
  cancer_type: CancerType;
  match: RegExp; // so khớp trên chữ đã bỏ dấu
  answer: string;
  doc_id: string;
}

export const FAQ: FaqEntry[] = [
  {
    cancer_type: "breast",
    match: /(nhu anh|mammo|ung thu vu|tam soat vu)/,
    answer:
      "Chụp nhũ ảnh là phương pháp tầm soát ung thư vú được khuyến nghị cho phụ nữ 40–74 tuổi có nguy cơ trung bình, thường 2 năm một lần. Khi chụp có thể hơi khó chịu do vú được ép nhẹ trong vài giây. Người có người thân mắc ung thư vú nên trao đổi với bác sĩ về kế hoạch riêng.",
    doc_id: "breast_uspstf_2024",
  },
  {
    cancer_type: "cervical",
    match: /(co tu cung|\bpap\b|\bhpv\b|phet te bao)/,
    answer:
      "Tầm soát ung thư cổ tử cung bắt đầu từ 21 tuổi: 21–29 tuổi làm xét nghiệm tế bào học (Pap) mỗi 3 năm; 30–65 tuổi có thể xét nghiệm HPV nguy cơ cao mỗi 5 năm. Người đã tiêm vắc-xin HPV vẫn nên tầm soát theo lịch.",
    doc_id: "cervical_uspstf_2018",
  },
  {
    cancer_type: "colorectal",
    match: /(dai truc trang|dai trang|noi soi|\bfit\b|mau an trong phan)/,
    answer:
      "Người 45–75 tuổi được khuyến nghị tầm soát ung thư đại trực tràng. Có nhiều lựa chọn: xét nghiệm tìm máu ẩn trong phân (FIT) hằng năm hoặc nội soi đại tràng mỗi 10 năm; bác sĩ sẽ cùng bạn chọn phương pháp phù hợp.",
    doc_id: "colorectal_uspstf_2021",
  },
  {
    cancer_type: "lung",
    match: /(ung thu phoi|ct lieu thap|ldct|chup phoi)/,
    answer:
      "Chụp CT phổi liều thấp hằng năm được khuyến nghị cho người 50–80 tuổi, có tiền sử hút thuốc từ 20 gói-năm và đang hút hoặc mới bỏ chưa quá 15 năm. Người không thuộc nhóm này thường không được khuyến nghị chụp định kỳ.",
    doc_id: "lung_uspstf_2021",
  },
  {
    cancer_type: "liver",
    match: /(ung thu gan|viem gan|xo gan|\bafp\b|sieu am gan)/,
    answer:
      "Người viêm gan B mạn hoặc xơ gan thuộc nhóm nguy cơ cao, nên được giám sát bằng siêu âm gan kèm xét nghiệm AFP khoảng mỗi 6 tháng theo chỉ định của bác sĩ.",
    doc_id: "liver_aasld_2023",
  },
  {
    cancer_type: "prostate",
    match: /(tien liet|\bpsa\b)/,
    answer:
      "Với nam giới 55–69 tuổi, xét nghiệm PSA định kỳ là quyết định cá nhân sau khi trao đổi lợi ích và nguy cơ với bác sĩ; guideline không quy định một tần suất cố định.",
    doc_id: "prostate_uspstf_2018",
  },
];

// ---------------------------------------------------------------- giáo dục
const edu = (
  cancer_type: CancerType,
  title: string,
  warning_signs: string[],
  prevention_tips: string[],
  body_md: string,
  doc_id: string,
): EducationContent => ({
  cancer_type,
  title,
  warning_signs,
  prevention_tips,
  body_md,
  sources: [GUIDELINE_SOURCES[doc_id]],
});

export const EDUCATION: EducationContent[] = [
  edu(
    "breast",
    "Tầm soát ung thư vú",
    ["Sờ thấy khối hoặc vùng dày lên ở vú, nách", "Núm vú tiết dịch hoặc máu", "Da vú lõm, sần như vỏ cam"],
    ["Duy trì cân nặng hợp lý", "Hạn chế rượu bia", "Vận động ít nhất 150 phút mỗi tuần"],
    "Chụp nhũ ảnh giúp phát hiện sớm những thay đổi ở mô vú trước khi có triệu chứng. Phụ nữ 40–74 tuổi có nguy cơ trung bình được khuyến nghị chụp định kỳ; người có tiền sử gia đình nên trao đổi với bác sĩ để có kế hoạch riêng.",
    "breast_uspstf_2024",
  ),
  edu(
    "cervical",
    "Tầm soát ung thư cổ tử cung",
    ["Ra máu âm đạo ngoài kỳ kinh hoặc sau quan hệ", "Khí hư bất thường kéo dài", "Đau vùng chậu kéo dài"],
    ["Tiêm vắc-xin HPV theo khuyến cáo", "Tầm soát định kỳ kể cả khi đã tiêm vắc-xin", "Quan hệ tình dục an toàn"],
    "Phần lớn ung thư cổ tử cung liên quan đến nhiễm HPV kéo dài. Xét nghiệm Pap và xét nghiệm HPV giúp phát hiện tổn thương tiền ung thư để xử trí sớm.",
    "cervical_uspstf_2018",
  ),
  edu(
    "colorectal",
    "Tầm soát ung thư đại trực tràng",
    ["Đi ngoài ra máu", "Thay đổi thói quen đại tiện kéo dài", "Sụt cân không rõ nguyên nhân"],
    ["Ăn nhiều rau xanh, chất xơ", "Hạn chế thịt đỏ và thịt chế biến sẵn", "Không hút thuốc"],
    "Tầm soát đại trực tràng có thể phát hiện và cắt bỏ polyp trước khi trở thành ung thư. Người 45–75 tuổi được khuyến nghị tầm soát bằng FIT hằng năm hoặc nội soi đại tràng định kỳ.",
    "colorectal_uspstf_2021",
  ),
  edu(
    "lung",
    "Tầm soát ung thư phổi",
    ["Ho kéo dài trên 3 tuần", "Ho ra máu", "Khó thở, đau ngực không rõ nguyên nhân"],
    ["Bỏ thuốc lá càng sớm càng tốt", "Tránh khói thuốc thụ động", "Hạn chế tiếp xúc khói bụi độc hại"],
    "Chụp CT phổi liều thấp dành cho người có tiền sử hút thuốc nhiều. Bỏ thuốc lá vẫn là biện pháp phòng ngừa hiệu quả nhất.",
    "lung_uspstf_2021",
  ),
  edu(
    "liver",
    "Giám sát ung thư gan",
    ["Vàng da, vàng mắt", "Đau tức vùng hạ sườn phải", "Bụng to dần, sụt cân"],
    ["Tiêm vắc-xin viêm gan B", "Điều trị và theo dõi viêm gan B/C theo chỉ định", "Hạn chế rượu bia"],
    "Người viêm gan B, C mạn hoặc xơ gan cần được bác sĩ theo dõi định kỳ bằng siêu âm gan và AFP để phát hiện sớm thay đổi bất thường.",
    "liver_aasld_2023",
  ),
  edu(
    "prostate",
    "Tầm soát ung thư tuyến tiền liệt",
    ["Tiểu khó, tiểu đêm nhiều lần", "Tiểu ra máu", "Đau lưng, hông kéo dài"],
    ["Duy trì cân nặng hợp lý", "Vận động đều đặn", "Trao đổi với bác sĩ trước khi làm xét nghiệm PSA"],
    "Xét nghiệm PSA có lợi ích và nguy cơ (phát hiện quá mức). Nam giới 55–69 tuổi nên trao đổi với bác sĩ để cùng quyết định.",
    "prostate_uspstf_2018",
  ),
];
