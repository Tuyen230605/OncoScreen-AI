/** Lỗi HTTP chuẩn hoá từ `{ detail }` của backend (hoặc từ mock). */
export class ApiRequestError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiRequestError";
  }
}

const STATUS_FALLBACK: Record<number, string> = {
  0: "Không kết nối được máy chủ. Vui lòng kiểm tra mạng và thử lại.",
  400: "Dữ liệu gửi lên chưa hợp lệ.",
  401: "Phiên đăng nhập hoặc mã truy cập không còn hiệu lực.",
  403: "Bạn không có quyền thực hiện thao tác này.",
  404: "Không tìm thấy dữ liệu.",
  409: "Trạng thái hiện tại không cho phép thao tác này. Vui lòng tải lại trang để xem trạng thái mới nhất.",
  422: "Dữ liệu gửi lên chưa hợp lệ. Vui lòng kiểm tra lại các trường đã nhập.",
  429: "Bạn đã gửi quá nhiều tin nhắn trong phiên này. Hãy bắt đầu cuộc trò chuyện mới.",
  500: "Máy chủ đang gặp sự cố. Vui lòng thử lại sau ít phút.",
  502: "Trợ lý AI tạm thời không phản hồi. Vui lòng thử lại sau ít phút.",
  503: "Hệ thống tạm thời không phản hồi. Vui lòng thử lại sau ít phút.",
};

/** JWT bị backend từ chối (hết hạn / không hợp lệ): phiên đăng nhập đã được xoá trên trình duyệt. */
export const SESSION_EXPIRED_MESSAGE = "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.";

/** Nhãn tiếng Việt cho tên trường trong lỗi validation của FastAPI/pydantic (`loc`). */
const FIELD_LABEL: Record<string, string> = {
  email: "Email",
  password: "Mật khẩu",
  full_name: "Họ và tên",
  age: "Tuổi",
  gender: "Giới tính",
  message: "Tin nhắn",
  answers: "Bảng hỏi",
  question: "Câu hỏi",
  history: "Lịch sử hội thoại",
  service_code: "Dịch vụ",
  preferred_date: "Ngày mong muốn",
  scheduled_date: "Ngày khám",
  reason: "Lý do khám",
  completed_at: "Ngày đã tầm soát",
  conclusion: "Kết luận",
  clinical_notes: "Ghi chú lâm sàng",
  final_plan: "Kế hoạch",
  items: "Kế hoạch",
  method: "Phương pháp",
  interval_months: "Chu kỳ (tháng)",
  next_due: "Ngày hẹn kế tiếp",
  rationale: "Lý do",
  general_advice: "Lời dặn chung",
};

type ValidationItem = { type?: unknown; loc?: unknown; msg?: unknown; ctx?: unknown };

function fieldOf(loc: unknown): string | null {
  if (!Array.isArray(loc)) return null;
  const names = loc.filter((x): x is string => typeof x === "string" && x !== "body" && x !== "query");
  const index = loc.find((x): x is number => typeof x === "number");
  const name = names.length ? names[names.length - 1] : null;
  if (!name) return null;
  const label = FIELD_LABEL[name] ?? name;
  return index !== undefined ? `${label} (mục ${index + 1})` : label;
}

/** Một lỗi validation → câu tiếng Việt. Thông điệp tự viết ở validator backend ("Value error, …") giữ nguyên. */
function validationMessage(item: ValidationItem): string | null {
  const msg = typeof item.msg === "string" ? item.msg : "";
  if (msg.startsWith("Value error, ")) return msg.slice("Value error, ".length);
  const ctx = item.ctx && typeof item.ctx === "object" ? (item.ctx as Record<string, unknown>) : {};
  const type = typeof item.type === "string" ? item.type : "";
  let problem: string;
  if (type === "missing") problem = "là bắt buộc";
  else if (type === "string_too_short")
    problem = Number(ctx.min_length) > 1 ? `tối thiểu ${String(ctx.min_length)} ký tự` : "không được để trống";
  else if (type === "string_too_long") problem = ctx.max_length ? `tối đa ${String(ctx.max_length)} ký tự` : "quá dài";
  else if (type.startsWith("int_")) problem = "phải là số nguyên";
  else if (type === "greater_than") problem = `phải lớn hơn ${String(ctx.gt)}`;
  else if (type === "greater_than_equal") problem = `phải từ ${String(ctx.ge)} trở lên`;
  else if (type === "less_than") problem = `phải nhỏ hơn ${String(ctx.lt)}`;
  else if (type === "less_than_equal") problem = `không được vượt quá ${String(ctx.le)}`;
  else if (type.startsWith("date") || type.startsWith("datetime")) problem = "không đúng định dạng ngày";
  else if (type === "too_long") problem = "có quá nhiều mục";
  else if (type === "too_short") problem = "cần ít nhất một mục";
  else problem = "chưa hợp lệ";
  const field = fieldOf(item.loc);
  return field ? `${field} ${problem}.` : null;
}

/**
 * `{ detail }` của backend → thông điệp hiển thị.
 * - chuỗi (400/403/404/409…): dùng nguyên văn;
 * - mảng lỗi validation (FastAPI 422): dịch từng lỗi sang tiếng Việt.
 */
export function messageFromDetail(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") return null;
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail.trim() || null;
  if (Array.isArray(detail)) {
    const msgs = detail
      .map((d) => (d && typeof d === "object" ? validationMessage(d as ValidationItem) : null))
      .filter((m): m is string => Boolean(m));
    return msgs.length ? Array.from(new Set(msgs)).join(" ") : null;
  }
  return null;
}

/** Thông điệp tiếng Việt hiển thị cho người dùng. */
export function errorMessage(err: unknown, fallback: string): string {
  if (err instanceof ApiRequestError) {
    return err.message || STATUS_FALLBACK[err.status] || fallback;
  }
  return fallback;
}

export function isStatus(err: unknown, status: number): boolean {
  return err instanceof ApiRequestError && err.status === status;
}

export function statusFallback(status: number): string | undefined {
  return STATUS_FALLBACK[status];
}
