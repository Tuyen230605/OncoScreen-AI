/** Mock handlers — cùng chữ ký với api.ts. Có delay nhỏ cho giống thật. */
import type { AnswersIn, EducationContent, LoginIn, Page, PatientDetail, PatientProfileIn, PatientProfileOut, RegisterIn, ReminderOut, ReviewIn, SessionOut, SessionSummary, TokenOut, UserOut } from "@/types/api";
import { DISCLAIMER, doctorUser, patientUser, plan, questionnaire, reminders, sessions } from "./fixtures";

const wait = <T,>(v: T, ms = 300) => new Promise<T>((r) => setTimeout(() => r(v), ms));
let profile: PatientProfileOut = { user_id: "u-lan", age: 45, gender: "female", genetics_history: ["breast_cancer_mother"], lifestyle: {}, lifestyle_score: null, updated_at: "2026-09-14T00:00:00Z" };

export const register = (b: RegisterIn) => wait<UserOut>({ ...patientUser, email: b.email, full_name: b.full_name, role: b.role });
export const login = (b: LoginIn) => wait<TokenOut>({ access_token: "mock-token", token_type: "bearer", user: b.email.startsWith("doctor") ? doctorUser : patientUser });
export const me = () => wait(patientUser);
export const getProfile = () => wait(profile);
export const putProfile = (b: PatientProfileIn) => wait((profile = { ...profile, ...b, updated_at: new Date().toISOString() }));

export const createSession = () => wait<SessionOut>({ ...sessions["s-collecting"], id: "s-new", questionnaire });
export const listSessions = (status?: string) => {
  const all = Object.values(sessions);
  const filtered = status ? all.filter((s) => s.status === status) : all;
  return wait<Page<SessionSummary>>({ items: filtered, total: filtered.length, page: 1, page_size: 20 });
};
export const getSession = (id: string) => wait<SessionOut>(sessions[id] ?? sessions["s-approved"]);
export const submitAnswers = (id: string, b: AnswersIn) => {
  const redFlag = b.answers.some((a) => a.question_id.startsWith("symptom_") && (a.value === true || a.value === "true"));
  if (redFlag) return wait<SessionOut>({ ...sessions["s-redflag"], id });
  const required = questionnaire.questions.filter((q) => q.required && !q.depends_on).map((q) => q.id);
  const answered = new Set(b.answers.map((a) => a.question_id));
  const complete = required.every((r) => answered.has(r));
  return wait<SessionOut>(complete ? { ...sessions["s-pending"], id, draft_plan: null } : { ...sessions["s-collecting"], id, answers: b.answers });
};
export const getPatientDetail = (id: string) => wait<PatientDetail>({ user: { ...patientUser, id }, profile, sessions: Object.values(sessions) });
export const review = (id: string, b: ReviewIn) =>
  wait<SessionOut>(b.action === "approve" ? { ...sessions["s-approved"], id, final_plan: b.final_plan ?? plan } : { ...sessions["s-pending"], id, status: "rejected", doctor_note: b.note ?? null });
export const listReminders = () => wait<ReminderOut[]>(reminders);
export const completeReminder = (id: string) => wait<ReminderOut>({ ...reminders[0], id, status: "done", completed_at: new Date().toISOString().slice(0, 10) });
export const getEducation = (type: string) =>
  wait<EducationContent>({ cancer_type: type as EducationContent["cancer_type"], title: `Hiểu về tầm soát ung thư ${type}`, warning_signs: ["Khối u bất thường", "Chảy máu bất thường", "Sụt cân không rõ nguyên nhân"], prevention_tips: ["Không hút thuốc", "Vận động đều đặn", "Tầm soát đúng lịch"], body_md: DISCLAIMER, sources: plan.items[0].sources });
