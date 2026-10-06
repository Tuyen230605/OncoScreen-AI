/**
 * Client HTTP duy nhất. Mọi component gọi API qua các hàm ở đây.
 * NEXT_PUBLIC_USE_MOCK_API=true → dùng src/mocks (không cần backend).
 */
import type {
  AnswersIn,
  EducationContent,
  LoginIn,
  Page,
  PatientDetail,
  PatientProfileIn,
  PatientProfileOut,
  RegisterIn,
  ReminderOut,
  ReviewIn,
  SessionOut,
  SessionSummary,
  TokenOut,
  UserOut,
} from "@/types/api";
import { getToken } from "@/lib/auth";
import * as mock from "@/mocks/handlers";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
export const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_API === "true";

export class ApiRequestError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json", ...(init.headers as Record<string, string>) };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = ((await res.json()) as { detail?: string }).detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new ApiRequestError(res.status, detail);
  }
  return (await res.json()) as T;
}

const qs = (o: Record<string, string | number | undefined>) => {
  const p = new URLSearchParams();
  Object.entries(o).forEach(([k, v]) => v !== undefined && p.set(k, String(v)));
  const s = p.toString();
  return s ? `?${s}` : "";
};

export const api = {
  // auth
  register: (b: RegisterIn) => (USE_MOCK ? mock.register(b) : request<UserOut>("/auth/register", { method: "POST", body: JSON.stringify(b) })),
  login: (b: LoginIn) => (USE_MOCK ? mock.login(b) : request<TokenOut>("/auth/login", { method: "POST", body: JSON.stringify(b) })),
  me: () => (USE_MOCK ? mock.me() : request<UserOut>("/auth/me")),

  // profile
  getProfile: () => (USE_MOCK ? mock.getProfile() : request<PatientProfileOut>("/patients/me/profile")),
  putProfile: (b: PatientProfileIn) =>
    USE_MOCK ? mock.putProfile(b) : request<PatientProfileOut>("/patients/me/profile", { method: "PUT", body: JSON.stringify(b) }),

  // sessions (patient)
  createSession: () => (USE_MOCK ? mock.createSession() : request<SessionOut>("/sessions", { method: "POST" })),
  listMySessions: (status?: string, page = 1) =>
    USE_MOCK ? mock.listSessions(status) : request<Page<SessionSummary>>(`/sessions${qs({ status, page })}`),
  getSession: (id: string) => (USE_MOCK ? mock.getSession(id) : request<SessionOut>(`/sessions/${id}`)),
  submitAnswers: (id: string, b: AnswersIn) =>
    USE_MOCK ? mock.submitAnswers(id, b) : request<SessionOut>(`/sessions/${id}/answers`, { method: "POST", body: JSON.stringify(b) }),

  // doctor
  listAllSessions: (status?: string, page = 1) =>
    USE_MOCK ? mock.listSessions(status) : request<Page<SessionSummary>>(`/doctor/sessions${qs({ status, page })}`),
  getPatientDetail: (id: string) => (USE_MOCK ? mock.getPatientDetail(id) : request<PatientDetail>(`/doctor/patients/${id}`)),
  review: (id: string, b: ReviewIn) =>
    USE_MOCK ? mock.review(id, b) : request<SessionOut>(`/sessions/${id}/review`, { method: "POST", body: JSON.stringify(b) }),

  // reminders
  listReminders: (status?: string) => (USE_MOCK ? mock.listReminders() : request<ReminderOut[]>(`/reminders${qs({ status })}`)),
  completeReminder: (id: string) =>
    USE_MOCK ? mock.completeReminder(id) : request<ReminderOut>(`/reminders/${id}/complete`, { method: "POST", body: "{}" }),

  // education
  getEducation: (type: string) => (USE_MOCK ? mock.getEducation(type) : request<EducationContent>(`/education/${type}`)),
};
