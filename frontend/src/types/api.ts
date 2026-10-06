/**
 * ★ CONTRACT — mirror của docs/protocols/API_CONTRACT.md và ai_core/ai_core/schemas.py.
 * KHÔNG tự thêm/sửa trường. Muốn đổi → PR `contract/*`.
 */

// ---------- enums
export type Role = "patient" | "doctor";
export type Gender = "male" | "female" | "other";
export type CancerType = "breast" | "cervical" | "colorectal" | "liver" | "lung" | "prostate" | "other";
export type RiskLevel = "average" | "elevated" | "high";
export type SessionStatus = "collecting" | "red_flag" | "pending_review" | "approved" | "rejected" | "completed";
export type QuestionType = "single_choice" | "multi_choice" | "number" | "boolean" | "text";
export type RedFlagSeverity = "urgent" | "soon";
export type ReminderStatus = "scheduled" | "due" | "done" | "skipped";

// ---------- auth
export interface UserOut {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  created_at: string;
}
export interface RegisterIn {
  email: string;
  password: string;
  full_name: string;
  role: Role;
}
export interface LoginIn {
  email: string;
  password: string;
}
export interface TokenOut {
  access_token: string;
  token_type: "bearer";
  user: UserOut;
}

// ---------- patient profile
export interface Lifestyle {
  smoking?: boolean;
  pack_years?: number;
  alcohol?: "none" | "light" | "heavy";
  height_cm?: number;
  weight_kg?: number;
  bmi?: number; // Vẫn giữ bmi nhưng sẽ tính tự động từ height/weight
  exercise?: "none" | "light" | "regular";
  [k: string]: unknown;
}
export interface PatientProfileIn {
  age: number;
  gender: Gender;
  genetics_history: string[];
  lifestyle: Lifestyle;
}
export interface PatientProfileOut extends PatientProfileIn {
  user_id: string;
  lifestyle_score: number | null;
  updated_at: string;
}

// ---------- questionnaire / answers
export interface Question {
  id: string;
  text: string;
  type: QuestionType;
  options: string[] | null;
  required: boolean;
  depends_on: string | null; // "question_id=value"
}
export interface Questionnaire {
  version: string;
  questions: Question[];
}
export interface Answer {
  question_id: string;
  value: unknown;
}

// ---------- AI outputs
export interface RedFlag {
  code: string;
  symptom: string;
  severity: RedFlagSeverity;
  advice: string;
}
export interface RedFlagResult {
  detected: boolean;
  flags: RedFlag[];
  message: string | null;
}
export interface Source {
  doc_id: string;
  title: string;
  section: string | null;
  excerpt: string;
  url: string | null;
}
export interface RiskFactor {
  cancer_type: CancerType;
  level: RiskLevel;
  reasons: string[];
}
export interface RiskAssessment {
  overall_summary: string;
  factors: RiskFactor[];
}
export interface PlanItem {
  cancer_type: CancerType;
  method: string;
  start_age: number | null;
  interval_months: number;
  next_due: string; // YYYY-MM-DD
  rationale: string;
  sources: Source[];
  priority: number;
}
export interface ScreeningPlan {
  items: PlanItem[];
  general_advice: string;
  generated_at: string;
  model: string;
}
export interface EducationContent {
  cancer_type: CancerType;
  title: string;
  warning_signs: string[];
  prevention_tips: string[];
  body_md: string;
  sources: Source[];
}

// ---------- sessions
export interface ReminderOut {
  id: string;
  session_id: string;
  patient_id: string;
  cancer_type: CancerType;
  method: string;
  due_date: string;
  status: ReminderStatus;
  completed_at: string | null;
  message: string | null;
}
export interface SessionSummary {
  id: string;
  patient_id: string;
  patient_name: string;
  status: SessionStatus;
  created_at: string;
  updated_at: string;
  has_red_flag: boolean;
}
export interface SessionOut extends SessionSummary {
  questionnaire: Questionnaire | null;
  answers: Answer[];
  red_flag: RedFlagResult | null;
  risk_assessment: RiskAssessment | null;
  draft_plan: ScreeningPlan | null; // chỉ doctor
  final_plan: ScreeningPlan | null; // patient: chỉ khi approved
  doctor_note: string | null;
  reviewed_by: UserOut | null;
  reviewed_at: string | null;
  disclaimer: string;
  reminders: ReminderOut[];
}
export interface AnswersIn {
  /** Có thể gửi từng phần; backend merge theo question_id. */
  answers: Answer[];
}
export interface ReviewIn {
  /** approve dùng draft_plan nếu final_plan không được gửi; reject bắt buộc note. */
  action: "approve" | "reject";
  final_plan?: ScreeningPlan;
  note?: string;
}
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
export interface PatientDetail {
  user: UserOut;
  profile: PatientProfileOut | null;
  sessions: SessionSummary[];
}
export interface ApiError {
  detail: string;
}
