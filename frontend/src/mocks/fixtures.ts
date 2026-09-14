/** Dữ liệu giả khớp contract — dùng khi NEXT_PUBLIC_USE_MOCK_API=true. Giữ đồng bộ với ai_core/mock.py. */
import type { Questionnaire, ReminderOut, ScreeningPlan, SessionOut, UserOut } from "@/types/api";

export const DISCLAIMER =
  "Thông tin trong hệ thống này chỉ mang tính giáo dục và tham khảo về tầm soát ung thư, KHÔNG phải chẩn đoán y khoa và không thay thế ý kiến của bác sĩ. Khuyến nghị (nếu có) đã được bác sĩ xem xét nhưng quyết định chỉ định tầm soát cụ thể thuộc về bác sĩ điều trị của bạn. Nếu bạn có triệu chứng bất thường, hãy đến cơ sở y tế để được khám trực tiếp.";

export const patientUser: UserOut = { id: "u-lan", email: "lan@demo.vn", full_name: "Trần Thị Lan", role: "patient", created_at: "2026-09-01T00:00:00Z" };
export const doctorUser: UserOut = { id: "u-doc", email: "doctor@demo.vn", full_name: "BS. Nguyễn Văn A", role: "doctor", created_at: "2026-09-01T00:00:00Z" };

export const questionnaire: Questionnaire = {
  version: "0.1",
  questions: [
    { id: "family_history", text: "Trong gia đình có ai từng mắc ung thư không?", type: "multi_choice", options: ["Không", "Ung thư vú", "Ung thư đại trực tràng", "Ung thư phổi", "Khác"], required: true, depends_on: null },
    { id: "smoking", text: "Bạn có đang hút thuốc hoặc từng hút thuốc không?", type: "boolean", options: null, required: true, depends_on: null },
    { id: "pack_years", text: "Ước tính số gói-năm?", type: "number", options: null, required: true, depends_on: "smoking=true" },
    { id: "symptom_lump", text: "Gần đây bạn có sờ thấy khối u hoặc cục bất thường không?", type: "boolean", options: null, required: true, depends_on: null },
    { id: "symptom_bleeding", text: "Bạn có bị chảy máu bất thường không?", type: "boolean", options: null, required: true, depends_on: null },
    { id: "symptom_weight_loss", text: "Bạn có sụt cân nhanh không rõ nguyên nhân không?", type: "boolean", options: null, required: true, depends_on: null },
  ],
};

export const plan: ScreeningPlan = {
  items: [
    {
      cancer_type: "breast",
      method: "Nhũ ảnh (mammography)",
      start_age: 40,
      interval_months: 12,
      next_due: "2026-10-14",
      rationale: "Nữ 40–74 tuổi nên chụp nhũ ảnh định kỳ; tiền sử gia đình → rút ngắn khoảng cách.",
      sources: [{ doc_id: "breast_uspstf_2024", title: "USPSTF 2024 — Breast Cancer Screening", section: "Recommendation", excerpt: "Biennial screening mammography for women aged 40 to 74 years.", url: "https://www.uspreventiveservicestaskforce.org/" }],
      priority: 1,
    },
    {
      cancer_type: "colorectal",
      method: "Nội soi đại tràng (hoặc FIT hàng năm)",
      start_age: 45,
      interval_months: 120,
      next_due: "2026-12-13",
      rationale: "Người 45–75 tuổi nên tầm soát ung thư đại trực tràng.",
      sources: [{ doc_id: "colorectal_uspstf_2021", title: "USPSTF 2021 — Colorectal Cancer Screening", section: null, excerpt: "Screening for colorectal cancer in all adults aged 45 to 75 years.", url: null }],
      priority: 3,
    },
  ],
  general_advice: "Duy trì lối sống lành mạnh; trao đổi với bác sĩ về kế hoạch phù hợp với bạn.",
  generated_at: "2026-09-14T08:00:00Z",
  model: "mock",
};

export const reminders: ReminderOut[] = [
  { id: "r1", session_id: "s-approved", patient_id: "u-lan", cancer_type: "breast", method: "Nhũ ảnh", due_date: "2026-10-14", status: "scheduled", completed_at: null, message: null },
];

const base = { patient_id: "u-lan", patient_name: "Trần Thị Lan", created_at: "2026-09-14T08:00:00Z", updated_at: "2026-09-14T08:00:00Z", answers: [], doctor_note: null, reviewed_by: null, reviewed_at: null, disclaimer: DISCLAIMER, reminders: [] as ReminderOut[] };

export const sessions: Record<string, SessionOut> = {
  "s-collecting": { ...base, id: "s-collecting", status: "collecting", has_red_flag: false, questionnaire, red_flag: null, risk_assessment: null, draft_plan: null, final_plan: null },
  "s-pending": { ...base, id: "s-pending", status: "pending_review", has_red_flag: false, questionnaire: null, red_flag: null, risk_assessment: null, draft_plan: plan, final_plan: null },
  "s-approved": { ...base, id: "s-approved", status: "approved", has_red_flag: false, questionnaire: null, red_flag: null, risk_assessment: { overall_summary: "Nguy cơ ung thư vú tăng do tiền sử gia đình.", factors: [{ cancer_type: "breast", level: "elevated", reasons: ["Nữ ≥ 40 tuổi", "Mẹ mắc ung thư vú"] }] }, draft_plan: plan, final_plan: plan, reviewed_by: doctorUser, reviewed_at: "2026-09-14T09:00:00Z", reminders },
  "s-redflag": { ...base, id: "s-redflag", status: "red_flag", has_red_flag: true, questionnaire: null, red_flag: { detected: true, flags: [{ code: "symptom_lump", symptom: "Sờ thấy khối u / cục bất thường", severity: "urgent", advice: "Hãy đến cơ sở y tế chuyên khoa để được khám trong vài ngày tới." }], message: "Bạn có dấu hiệu cần được bác sĩ khám trực tiếp sớm. Hệ thống tạm dừng tư vấn tầm soát định kỳ." }, risk_assessment: null, draft_plan: null, final_plan: null },
};
