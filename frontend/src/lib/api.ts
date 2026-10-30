/**
 * Client HTTP duy nhất — phủ toàn bộ endpoint trong docs/protocols/API_CONTRACT.md.
 * Mọi component gọi API qua `api.*`; type chỉ lấy từ src/types/api.ts.
 * NEXT_PUBLIC_USE_MOCK_API=true → dùng src/mocks (demo offline đủ 4 giai đoạn, không cần backend).
 *
 * Xác thực:
 * - `Authorization: Bearer <JWT>` tự gắn khi đã đăng nhập.
 * - Endpoint Navigator nhận thêm `X-Consult-Token` cho phiên tư vấn ẩn danh. Bearer chỉ gửi kèm khi người dùng là
 *   bệnh nhân (contract: "tuỳ chọn Bearer (patient)").
 * - JWT bị từ chối (hết hạn) → xoá phiên + phát sự kiện `onSessionExpired` (RoleGuard chuyển về /login?next=…);
 *   riêng các endpoint Navigator thử lại 1 lần ở chế độ ẩn danh.
 */
import type {
  AgentName,
  AgentRunOut,
  AppointmentIn,
  AppointmentOut,
  AppointmentStatus,
  CancerType,
  ConfirmAppointmentIn,
  ConsultationCreated,
  ConsultationOut,
  CopilotAskIn,
  EducationContent,
  EncounterOut,
  FinalizeEncounterIn,
  LoginIn,
  MetricsOut,
  NavigatorMessageIn,
  Page,
  PatientListItem,
  PatientProfileIn,
  PatientProfileOut,
  PatientRecordOut,
  QuestionAnswer,
  Questionnaire,
  RegisterIn,
  ReminderOut,
  ReminderStatus,
  ServiceOut,
  TokenOut,
  UserOut,
} from "@/types/api";
import { expireSession, getToken, getUser } from "@/lib/auth";
import { ApiRequestError, messageFromDetail, SESSION_EXPIRED_MESSAGE, statusFallback } from "@/lib/errors";
import * as mock from "@/mocks/handlers";

export { ApiRequestError } from "@/lib/errors";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
export const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_API === "true";

/** `GET /education` trả `{ cancer_type, title }[]` (contract chưa đặt tên type). */
export type EducationTopic = { cancer_type: CancerType; title: string };
/** `GET /health` (contract chưa có type trong src/types/api.ts). */
export type HealthOut = { status: string; agent: "mock" | "real"; db: string };

interface RequestOptions {
  method?: "GET" | "POST" | "PUT";
  body?: unknown;
  /** Gửi Bearer nếu có token (mặc định true). */
  auth?: boolean;
  consultToken?: string | null;
  /** Navigator: JWT bị từ chối → xoá phiên rồi thử lại 1 lần ở chế độ ẩn danh (không Bearer). */
  anonymousRetry?: boolean;
}

/**
 * 401 cũng có thể do mã phiên tư vấn (X-Consult-Token) sai trong khi JWT vẫn hợp lệ.
 * Chỉ coi là hết phiên đăng nhập khi `GET /auth/me` với chính token đó cũng bị từ chối.
 */
async function bearerRejected(path: string, token: string): Promise<boolean> {
  if (path === "/auth/me") return true;
  try {
    const res = await fetch(`${BASE}/auth/me`, {
      headers: { Accept: "application/json", Authorization: `Bearer ${token}` },
    });
    return res.status === 401;
  } catch {
    return false; // lỗi mạng: không kết luận được, giữ phiên
  }
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (opts.body !== undefined) headers["Content-Type"] = "application/json";
  const sentToken = opts.auth !== false ? getToken() : null;
  if (sentToken) headers.Authorization = `Bearer ${sentToken}`;
  if (opts.consultToken) headers["X-Consult-Token"] = opts.consultToken;

  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      method: opts.method ?? "GET",
      headers,
      body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
    });
  } catch {
    throw new ApiRequestError(0, statusFallback(0) ?? "Không kết nối được máy chủ.");
  }
  if (!res.ok) {
    if (res.status === 401 && sentToken && (await bearerRejected(path, sentToken))) {
      expireSession(sentToken);
      if (opts.anonymousRetry) return request<T>(path, { ...opts, auth: false, anonymousRetry: false });
      throw new ApiRequestError(401, SESSION_EXPIRED_MESSAGE);
    }
    let detail: string | null = null;
    try {
      detail = messageFromDetail(await res.json());
    } catch {
      /* body không phải JSON */
    }
    throw new ApiRequestError(res.status, detail ?? statusFallback(res.status) ?? res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

const qs = (o: Record<string, string | number | undefined | null>) => {
  const p = new URLSearchParams();
  Object.entries(o).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") p.set(k, String(v));
  });
  const s = p.toString();
  return s ? `?${s}` : "";
};

/** Navigator: chỉ gửi Bearer khi người dùng đăng nhập là bệnh nhân. */
const navigatorAuth = () => getUser()?.role === "patient";

export const api = {
  // ---------- health
  health: () => (USE_MOCK ? mock.health() : request<HealthOut>("/health", { auth: false })),

  // ---------- 1. Navigator (công khai)
  getNavigatorQuestionnaire: () =>
    USE_MOCK ? mock.getNavigatorQuestionnaire() : request<Questionnaire>("/navigator/questionnaire", { auth: false }),
  createConsultation: () =>
    USE_MOCK
      ? mock.createConsultation()
      : request<ConsultationCreated>("/navigator/consultations", {
          method: "POST",
          auth: navigatorAuth(),
          anonymousRetry: true,
        }),
  getConsultation: (id: string, consultToken?: string | null) =>
    USE_MOCK
      ? mock.getConsultation(id, consultToken)
      : request<ConsultationOut>(`/navigator/consultations/${encodeURIComponent(id)}`, {
          auth: navigatorAuth(),
          consultToken,
          anonymousRetry: true,
        }),
  sendConsultMessage: (id: string, body: NavigatorMessageIn, consultToken?: string | null) =>
    USE_MOCK
      ? mock.sendConsultMessage(id, body, consultToken)
      : request<ConsultationOut>(`/navigator/consultations/${encodeURIComponent(id)}/messages`, {
          method: "POST",
          body,
          auth: navigatorAuth(),
          consultToken,
          anonymousRetry: true,
        }),
  /** Gắn phiên ẩn danh vào tài khoản bệnh nhân đã có (Bearer + X-Consult-Token). */
  claimConsultation: (id: string, consultToken: string) =>
    USE_MOCK
      ? mock.claimConsultation(id, consultToken)
      : request<ConsultationOut>(`/navigator/consultations/${encodeURIComponent(id)}/claim`, {
          method: "POST",
          consultToken,
        }),
  listServices: () => (USE_MOCK ? mock.listServices() : request<ServiceOut[]>("/services", { auth: false })),
  listEducationTopics: () =>
    USE_MOCK ? mock.listEducationTopics() : request<EducationTopic[]>("/education", { auth: false }),
  getEducation: (type: CancerType) =>
    USE_MOCK ? mock.getEducation(type) : request<EducationContent>(`/education/${type}`, { auth: false }),

  // ---------- 2. Auth
  register: (b: RegisterIn) =>
    USE_MOCK ? mock.register(b) : request<UserOut>("/auth/register", { method: "POST", body: b, auth: false }),
  login: (b: LoginIn) =>
    USE_MOCK ? mock.login(b) : request<TokenOut>("/auth/login", { method: "POST", body: b, auth: false }),
  me: () => (USE_MOCK ? mock.me() : request<UserOut>("/auth/me")),

  // ---------- 3. Bệnh nhân
  getProfile: () => (USE_MOCK ? mock.getProfile() : request<PatientProfileOut>("/patients/me/profile")),
  putProfile: (b: PatientProfileIn) =>
    USE_MOCK
      ? mock.putProfile(b)
      : request<PatientProfileOut>("/patients/me/profile", { method: "PUT", body: b }),
  getMyRecord: () => (USE_MOCK ? mock.getMyRecord() : request<PatientRecordOut>("/patients/me/record")),
  createAppointment: (b: AppointmentIn) =>
    USE_MOCK ? mock.createAppointment(b) : request<AppointmentOut>("/appointments", { method: "POST", body: b }),
  listMyAppointments: () => (USE_MOCK ? mock.listMyAppointments() : request<AppointmentOut[]>("/appointments")),
  cancelAppointment: (id: string) =>
    USE_MOCK
      ? mock.cancelAppointment(id)
      : request<AppointmentOut>(`/appointments/${encodeURIComponent(id)}/cancel`, { method: "POST" }),
  getEncounter: (id: string) =>
    USE_MOCK ? mock.getEncounter(id) : request<EncounterOut>(`/encounters/${encodeURIComponent(id)}`),
  askEncounterQuestion: (id: string, question: string) =>
    USE_MOCK
      ? mock.askEncounterQuestion(id, question)
      : request<QuestionAnswer>(`/encounters/${encodeURIComponent(id)}/questions`, {
          method: "POST",
          body: { question },
        }),
  listReminders: (status?: ReminderStatus) =>
    USE_MOCK ? mock.listReminders(status) : request<ReminderOut[]>(`/reminders${qs({ status })}`),
  completeReminder: (id: string, completedAt?: string) =>
    USE_MOCK
      ? mock.completeReminder(id, completedAt)
      : request<ReminderOut>(`/reminders/${encodeURIComponent(id)}/complete`, {
          method: "POST",
          body: completedAt ? { completed_at: completedAt } : {},
        }),

  // ---------- 4. Bác sĩ — Clinical Copilot & HITL
  listDoctorAppointments: (status?: AppointmentStatus, page = 1) =>
    USE_MOCK
      ? mock.listDoctorAppointments(status, page)
      : request<Page<AppointmentOut>>(`/doctor/appointments${qs({ status, page })}`),
  confirmAppointment: (id: string, b: ConfirmAppointmentIn) =>
    USE_MOCK
      ? mock.confirmAppointment(id, b)
      : request<AppointmentOut>(`/doctor/appointments/${encodeURIComponent(id)}/confirm`, { method: "POST", body: b }),
  startAppointment: (id: string) =>
    USE_MOCK
      ? mock.startAppointment(id)
      : request<EncounterOut>(`/doctor/appointments/${encodeURIComponent(id)}/start`, { method: "POST" }),
  listPatients: (q?: string) =>
    USE_MOCK ? mock.listPatients(q) : request<PatientListItem[]>(`/doctor/patients${qs({ q })}`),
  getPatientRecord: (id: string) =>
    USE_MOCK
      ? mock.getPatientRecord(id)
      : request<PatientRecordOut>(`/doctor/patients/${encodeURIComponent(id)}/record`),
  getDoctorEncounter: (id: string) =>
    USE_MOCK ? mock.getDoctorEncounter(id) : request<EncounterOut>(`/doctor/encounters/${encodeURIComponent(id)}`),
  regenerateBrief: (id: string) =>
    USE_MOCK
      ? mock.regenerateBrief(id)
      : request<EncounterOut>(`/doctor/encounters/${encodeURIComponent(id)}/brief`, { method: "POST" }),
  askCopilot: (id: string, b: CopilotAskIn) =>
    USE_MOCK
      ? mock.askCopilot(id, b)
      : request<QuestionAnswer>(`/doctor/encounters/${encodeURIComponent(id)}/copilot`, { method: "POST", body: b }),
  finalizeEncounter: (id: string, b: FinalizeEncounterIn) =>
    USE_MOCK
      ? mock.finalizeEncounter(id, b)
      : request<EncounterOut>(`/doctor/encounters/${encodeURIComponent(id)}/finalize`, { method: "POST", body: b }),
  getMetrics: () => (USE_MOCK ? mock.getMetrics() : request<MetricsOut>("/doctor/metrics")),
  listAgentRuns: (agent?: AgentName, page = 1) =>
    USE_MOCK
      ? mock.listAgentRuns(agent, page)
      : request<Page<AgentRunOut>>(`/doctor/agent-runs${qs({ agent, page })}`),
  listDueReminders: () => (USE_MOCK ? mock.listDueReminders() : request<ReminderOut[]>("/doctor/reminders/due")),
};
