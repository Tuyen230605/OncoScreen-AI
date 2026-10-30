/** Nhãn tiếng Việt cho các enum trong contract (chỉ hiển thị, không suy luận y khoa). */
import type {
  AgentName,
  AppointmentStatus,
  BookingPriority,
  CancerType,
  EncounterStatus,
  Gender,
  NextAction,
  ReminderStatus,
  RiskLevel,
} from "@/types/api";

export const CANCER_LABEL: Record<CancerType, string> = {
  breast: "Ung thư vú",
  cervical: "Ung thư cổ tử cung",
  colorectal: "Ung thư đại trực tràng",
  liver: "Ung thư gan",
  lung: "Ung thư phổi",
  prostate: "Ung thư tuyến tiền liệt",
  other: "Ung thư khác",
};

export const GENDER_LABEL: Record<Gender, string> = {
  female: "Nữ",
  male: "Nam",
  other: "Khác",
};

export const RISK_LEVEL_LABEL: Record<RiskLevel, string> = {
  average: "Nguy cơ trung bình",
  elevated: "Nguy cơ tăng",
  high: "Nguy cơ cao",
};

export const APPOINTMENT_STATUS_LABEL: Record<AppointmentStatus, string> = {
  requested: "Chờ xác nhận",
  confirmed: "Đã xác nhận",
  completed: "Đã khám",
  cancelled: "Đã huỷ",
};

export const ENCOUNTER_STATUS_LABEL: Record<EncounterStatus, string> = {
  in_progress: "Đang khám",
  finalized: "Đã hoàn tất",
};

export const REMINDER_STATUS_LABEL: Record<ReminderStatus, string> = {
  scheduled: "Sắp tới",
  due: "Đến hạn",
  done: "Đã hoàn thành",
  skipped: "Đã bỏ qua",
};

export const PRIORITY_LABEL: Record<BookingPriority, string> = {
  routine: "Thường quy",
  urgent: "Ưu tiên",
};

export const NEXT_ACTION_LABEL: Record<NextAction, string> = {
  continue_chat: "Tiếp tục trò chuyện",
  suggest_booking: "Gợi ý đặt lịch",
  urgent_care: "Cần khám sớm",
};

export const AGENT_LABEL: Record<AgentName, string> = {
  navigator: "Navigator",
  copilot: "Copilot brief",
  copilot_qa: "Copilot hỏi đáp",
  patient_qa: "Hỏi đáp bệnh nhân",
};

export const MISSING_INFO_LABEL: Record<string, string> = {
  age: "Tuổi của bạn",
  gender: "Giới tính",
  pack_years: "Số gói-năm đã hút (số gói/ngày × số năm)",
};

export const SYMPTOM_LABEL: Record<string, string> = {
  symptom_lump: "Sờ thấy khối/cục bất thường",
  symptom_bleeding: "Chảy máu bất thường",
  symptom_weight_loss: "Sụt cân không rõ nguyên nhân",
  symptom_persistent_pain: "Đau kéo dài",
  symptom_bowel_change: "Thay đổi thói quen đại tiện",
  symptom_jaundice: "Vàng da, vàng mắt",
};

export const EVENT_KIND_LABEL: Record<string, string> = {
  "account.created": "Tạo tài khoản",
  "consult.summary": "Tóm tắt tư vấn",
  "red_flag.detected": "Dấu hiệu cần khám sớm",
  "appointment.requested": "Yêu cầu đặt lịch",
  "appointment.confirmed": "Lịch hẹn được xác nhận",
  "appointment.cancelled": "Lịch hẹn đã huỷ",
  "appointment.escalated": "Lịch hẹn chuyển sang ưu tiên",
  "appointment.completed": "Hoàn tất lịch hẹn",
  "encounter.started": "Bắt đầu khám",
  "encounter.finalized": "Bác sĩ kết luận",
  "reminder.due": "Nhắc lịch đến hạn",
  "reminder.done": "Đã tầm soát theo nhắc lịch",
  "profile.updated": "Cập nhật hồ sơ",
};

export function eventKindLabel(kind: string): string {
  return EVENT_KIND_LABEL[kind] ?? kind;
}

export function cancerLabel(type: CancerType): string {
  return CANCER_LABEL[type] ?? type;
}

export const RELATIVE_LABEL: Record<string, string> = {
  mother: "Mẹ",
  father: "Bố",
  sister: "Chị/em gái",
  brother: "Anh/em trai",
  daughter: "Con gái",
  son: "Con trai",
  relative: "Người thân khác",
  family: "Người thân",
};

/** Mã tiền sử gia đình theo contract: "<cancer_type>_cancer_<người thân>" (vd. "breast_cancer_family" từ phiên tư vấn). */
export function geneticsLabel(code: string): string {
  const [type, relative] = code.split("_cancer_");
  const cancer = CANCER_LABEL[type as CancerType];
  if (!cancer) return code;
  return `${cancer}: ${RELATIVE_LABEL[relative] ?? relative ?? "người thân"}`;
}

/** Hiển thị trước khi có phản hồi đầu tiên từ API (sau đó luôn dùng `disclaimer` do API trả về). */
export const DEFAULT_DISCLAIMER =
  "Thông tin trong hệ thống này chỉ mang tính giáo dục và tham khảo về tầm soát ung thư, KHÔNG phải chẩn đoán y khoa và không thay thế ý kiến của bác sĩ. Kế hoạch tầm soát cá nhân chỉ có hiệu lực khi đã được bác sĩ xem xét và phê duyệt. Nếu bạn có triệu chứng bất thường, hãy đến cơ sở y tế để được khám trực tiếp.";

/** Lưu ý cho bác sĩ (mirror `COPILOT_DISCLAIMER_VI` của backend) khi trang không có `disclaimer` từ API. */
export const COPILOT_DEFAULT_DISCLAIMER =
  "Công cụ hỗ trợ ra quyết định lâm sàng: tóm tắt hồ sơ và đối chiếu guideline có trích dẫn. AI không chẩn đoán và không diễn giải kết quả cận lâm sàng; bác sĩ chịu trách nhiệm chẩn đoán, chỉ định và phê duyệt kế hoạch trước khi gửi bệnh nhân.";
