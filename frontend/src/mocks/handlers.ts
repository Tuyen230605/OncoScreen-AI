/**
 * Mock handlers — cùng chữ ký với `api.*` trong src/lib/api.ts.
 * Một "backend" nhỏ trong trình duyệt: DB in-memory (lưu localStorage, bọc try/catch) mô phỏng đủ 4 giai đoạn:
 * Navigator ẩn danh → đăng ký & đặt lịch → bác sĩ khám với Copilot → bệnh nhân theo dõi.
 * Quy tắc phân quyền & lộ dữ liệu bám theo docs/protocols/API_CONTRACT.md.
 *
 * Tài khoản demo (mật khẩu 123456): lan@demo.vn, minh@demo.vn, hoa@demo.vn, tuan@demo.vn, doctor@demo.vn.
 */
import type {
  AgentName,
  AgentRunOut,
  Answer,
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
  IntakeProfile,
  LoginIn,
  MetricsOut,
  NavigatorMessageIn,
  NavigatorReply,
  Page,
  PatientListItem,
  PatientProfileIn,
  PatientProfileOut,
  PatientRecordOut,
  QuestionAnswer,
  Questionnaire,
  RecordEventOut,
  RegisterIn,
  ReminderOut,
  ReminderStatus,
  ScreeningPlan,
  ServiceOut,
  TokenOut,
  TraceEvent,
  UserOut,
} from "@/types/api";
import { getToken } from "@/lib/auth";
import { ApiRequestError } from "@/lib/errors";
import { addDaysISO, parseISODate, todayISO } from "@/lib/format";
import {
  DISCLAIMER,
  EDUCATION,
  LABEL_VI,
  MAX_CONSULT_TURNS,
  MOCK_PASSWORD,
  NAVIGATOR_QUESTIONNAIRE,
  SERVICES,
} from "./fixtures";
import {
  assertNavigatorInvariants,
  buildBrief,
  copilotAnswer,
  emptyIntake,
  intakeFromAnswers,
  intakeFromProfile,
  intakeFromText,
  newId,
  newTraceId,
  patientPlanAnswer,
  runNavigator,
} from "./engine";

// ================================================================ DB
interface MockUser extends UserOut {
  password: string;
}
interface ConsultRow {
  consultation: ConsultationOut;
  token: string;
  owner_id: string | null;
}
interface MockDb {
  version: number;
  users: MockUser[];
  profiles: Record<string, PatientProfileOut>;
  consultations: ConsultRow[];
  appointments: AppointmentOut[];
  encounters: EncounterOut[];
  editedEncounterIds: string[];
  reminders: ReminderOut[];
  events: Record<string, RecordEventOut[]>; // theo bệnh nhân, thứ tự thời gian tăng dần
  agentRuns: AgentRunOut[];
}

const DB_VERSION = 4;
const DB_KEY = "cs_mock_db";
const PAGE_SIZE = 20;

let db: MockDb | null = null;

function storage(): Storage | null {
  try {
    return typeof window !== "undefined" ? window.localStorage : null;
  } catch {
    return null;
  }
}

function getDb(): MockDb {
  if (db) return db;
  try {
    const raw = storage()?.getItem(DB_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as MockDb;
      if (parsed.version === DB_VERSION) {
        db = parsed;
        return db;
      }
    }
  } catch {
    /* dữ liệu hỏng hoặc storage bị chặn → seed lại */
  }
  db = seed();
  persist();
  return db;
}

function persist(): void {
  try {
    if (db) storage()?.setItem(DB_KEY, JSON.stringify(db));
  } catch {
    /* storage đầy/bị chặn: dữ liệu demo chỉ sống trong tab hiện tại */
  }
}

/** Xoá dữ liệu demo (dùng cho nút "Khôi phục dữ liệu demo" nếu cần). */
export function resetMockDb(): void {
  db = seed();
  persist();
}

const clone = <T,>(v: T): T => JSON.parse(JSON.stringify(v)) as T;
function fail(status: number, detail: string): never {
  throw new ApiRequestError(status, detail);
}

/** Chạy logic đồng bộ, trả kết quả sau một độ trễ nhỏ cho giống mạng thật. */
function respond<T>(fn: () => T, ms = 250): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    setTimeout(() => {
      try {
        const out = fn();
        persist();
        resolve(clone(out));
      } catch (err) {
        if (!(err instanceof ApiRequestError)) console.error("[mock]", err);
        reject(err instanceof ApiRequestError ? err : new ApiRequestError(500, "Lỗi mock nội bộ."));
      }
    }, ms);
  });
}

const nowIso = () => new Date().toISOString();
const atDay = (offsetDays: number, hour = 9): string => {
  const d = parseISODate(addDaysISO(todayISO(), offsetDays));
  d.setHours(hour, 0, 0, 0);
  return d.toISOString();
};
const randomToken = () => `${newTraceId()}${newTraceId()}`;
const publicUser = (u: MockUser): UserOut => ({
  id: u.id,
  email: u.email,
  full_name: u.full_name,
  role: u.role,
  created_at: u.created_at,
});
const serviceName = (code: string) => SERVICES.find((s) => s.code === code)?.name ?? code;

// ================================================================ auth helpers
function optionalUser(): MockUser | null {
  const token = getToken();
  if (!token?.startsWith("mock-token:")) return null;
  const id = token.slice("mock-token:".length);
  return getDb().users.find((u) => u.id === id) ?? null;
}
function requireUser(): MockUser {
  return optionalUser() ?? fail(401, "Bạn cần đăng nhập để tiếp tục.");
}
function requirePatient(): MockUser {
  const u = requireUser();
  return u.role === "patient" ? u : fail(403, "Chức năng dành cho bệnh nhân.");
}
function requireDoctor(): MockUser {
  const u = requireUser();
  return u.role === "doctor" ? u : fail(403, "Chức năng dành cho bác sĩ.");
}

// ================================================================ record / events
function addEvent(
  patientId: string,
  kind: string,
  summary: string,
  data: Record<string, unknown> = {},
  at: string = nowIso(),
): RecordEventOut {
  const d = getDb();
  const event: RecordEventOut = { id: newId("ev"), at, kind, summary, data };
  (d.events[patientId] ??= []).push(event);
  return event;
}

function eventsOf(patientId: string): RecordEventOut[] {
  return [...(getDb().events[patientId] ?? [])].sort((a, b) => a.at.localeCompare(b.at));
}

function refreshReminders(): void {
  const today = todayISO();
  getDb().reminders.forEach((r) => {
    if (r.status === "scheduled" && r.due_date <= today) {
      r.status = "due";
      r.message = r.message ?? `Đã đến hạn ${r.method.toLowerCase()} theo kế hoạch bác sĩ đã duyệt.`;
      addEvent(r.patient_id, "reminder.due", `Đến hạn: ${r.method} (${LABEL_VI[r.cancer_type]}).`, {
        reminder_id: r.id,
      });
    }
  });
}

/** Góc nhìn bệnh nhân: không bao giờ có brief / draft_plan / clinical_notes; kết quả chỉ khi finalized. */
function patientView(e: EncounterOut): EncounterOut {
  const finalized = e.status === "finalized";
  return {
    ...e,
    brief: null,
    draft_plan: null,
    clinical_notes: null,
    final_plan: finalized ? e.final_plan : null,
    conclusion: finalized ? e.conclusion : null,
    reminders: finalized ? e.reminders : [],
  };
}

function encounterWithReminders(e: EncounterOut): EncounterOut {
  return { ...e, reminders: getDb().reminders.filter((r) => r.encounter_id === e.id) };
}

function recordFor(patientId: string, view: "patient" | "doctor"): PatientRecordOut {
  const d = getDb();
  refreshReminders();
  const user = d.users.find((u) => u.id === patientId && u.role === "patient") ?? fail(404, "Không tìm thấy bệnh nhân.");
  // Như backend (record_service.record_out): bệnh nhân chỉ thấy lượt khám đã hoàn tất
  const encounters = d.encounters
    .filter((e) => e.patient_id === patientId && (view === "doctor" || e.status === "finalized"))
    .map(encounterWithReminders)
    .map((e) => (view === "patient" ? patientView(e) : e))
    .sort((a, b) => b.created_at.localeCompare(a.created_at));
  return {
    user: publicUser(user),
    profile: d.profiles[patientId] ?? null,
    consultations: d.consultations
      .filter((c) => c.owner_id === patientId)
      .map((c) => c.consultation)
      .sort((a, b) => b.created_at.localeCompare(a.created_at)),
    appointments: d.appointments
      .filter((a) => a.patient_id === patientId)
      .sort((a, b) => b.created_at.localeCompare(a.created_at)),
    encounters,
    reminders: d.reminders.filter((r) => r.patient_id === patientId).sort((a, b) => a.due_date.localeCompare(b.due_date)),
    timeline: eventsOf(patientId).reverse(),
  };
}

// ================================================================ agent runs
function logRun(
  agent: AgentName,
  patientId: string | null,
  traceId: string,
  events: TraceEvent[],
  extra: Partial<Pick<AgentRunOut, "red_flag" | "next_action" | "insufficient_evidence" | "guard_blocked">> = {},
  latency?: number,
  at: string = nowIso(),
): void {
  getDb().agentRuns.push({
    id: newId("run"),
    agent,
    trace_id: traceId,
    patient_id: patientId,
    latency_ms: latency ?? 90 + Math.round(Math.random() * 700),
    generator: "template",
    red_flag: extra.red_flag ?? false,
    next_action: extra.next_action ?? null,
    insufficient_evidence: extra.insufficient_evidence ?? false,
    guard_blocked: extra.guard_blocked ?? false,
    events,
    created_at: at,
  });
}

// ================================================================ consultation helpers
function summarizeAnswers(answers: Answer[]): string {
  return `Đã trả lời bảng hỏi nhanh (${answers.length} câu).`;
}

function intakeSummary(intake: IntakeProfile): string {
  const parts: string[] = [];
  if (intake.gender) parts.push(intake.gender === "female" ? "nữ" : intake.gender === "male" ? "nam" : "giới tính khác");
  if (intake.age !== null) parts.push(`${intake.age} tuổi`);
  if (intake.family_history.length) {
    parts.push(`người thân mắc ${intake.family_history.map((t) => LABEL_VI[t]).join(", ")}`);
  }
  if (intake.smoking) parts.push(intake.pack_years !== null ? `hút thuốc ${intake.pack_years} gói-năm` : "có hút thuốc");
  if (intake.hepatitis_b_or_c) parts.push("viêm gan B/C mạn");
  if (intake.cirrhosis) parts.push("xơ gan");
  if (intake.personal_cancer_history) parts.push("từng được chẩn đoán ung thư");
  return parts.join("; ");
}

function consultSummaryText(c: ConsultationOut): string {
  const reply = c.last_reply;
  const who = intakeSummary(c.intake) || "chưa đủ thông tin nhân khẩu";
  const suggested = reply?.suggestions.length
    ? ` Gợi ý tầm soát theo guideline: ${reply.suggestions.map((s) => LABEL_VI[s.cancer_type]).join(", ")}.`
    : "";
  return `Tư vấn trực tuyến: ${who}.${suggested}`;
}

/** Gắn phiên tư vấn vào tài khoản: điền sẵn hồ sơ (nếu đủ tuổi + giới) và ghi mốc vào hồ sơ xuyên suốt. */
function linkConsultation(row: ConsultRow, patientId: string, at: string = nowIso()): void {
  const d = getDb();
  row.owner_id = patientId;
  row.consultation.linked = true;
  row.consultation.updated_at = at;
  const intake = row.consultation.intake;
  if (!d.profiles[patientId] && intake.age !== null && intake.gender !== null) {
    d.profiles[patientId] = {
      user_id: patientId,
      age: intake.age,
      gender: intake.gender,
      genetics_history: intake.family_history.map((t) => `${t}_cancer_relative`),
      lifestyle: {
        ...(intake.smoking !== null ? { smoking: intake.smoking } : {}),
        ...(intake.pack_years !== null ? { pack_years: intake.pack_years } : {}),
        ...(intake.hepatitis_b_or_c !== null ? { hepatitis_b_or_c: intake.hepatitis_b_or_c } : {}),
        ...(intake.cirrhosis !== null ? { cirrhosis: intake.cirrhosis } : {}),
      },
      lifestyle_score: null,
      updated_at: at,
    };
  }
  addEvent(
    patientId,
    "consult.summary",
    consultSummaryText(row.consultation),
    {
      consultation_id: row.consultation.id,
      cancer_types: row.consultation.last_reply?.suggestions.map((s) => s.cancer_type) ?? [],
    },
    at,
  );
  const rf = row.consultation.last_reply?.red_flag;
  if (rf?.detected) {
    addEvent(
      patientId,
      "red_flag.detected",
      `Ghi nhận khi tư vấn: ${rf.flags.map((f) => f.symptom.toLowerCase()).join(", ")}.`,
      { consultation_id: row.consultation.id, codes: rf.flags.map((f) => f.code) },
      at,
    );
  }
}

function accessConsult(id: string, consultToken?: string | null): ConsultRow {
  const row = getDb().consultations.find((c) => c.consultation.id === id) ?? fail(404, "Không tìm thấy phiên tư vấn.");
  if (row.owner_id) {
    const u = optionalUser();
    if (u?.id === row.owner_id) return row;
    return fail(401, "Phiên tư vấn đã gắn với tài khoản. Vui lòng đăng nhập bằng tài khoản đó.");
  }
  if (!consultToken || consultToken !== row.token) return fail(401, "Mã truy cập phiên tư vấn không hợp lệ.");
  return row;
}

/** Xử lý một lượt Navigator (dùng cả khi seed dữ liệu). */
function processTurn(row: ConsultRow, body: NavigatorMessageIn, at: string = nowIso()): void {
  const c = row.consultation;
  const message = body.message?.trim() || null;
  const answers = body.answers ?? [];
  let intake = c.intake;
  if (answers.length) intake = intakeFromAnswers(intake, answers);
  if (message) intake = intakeFromText(intake, message);
  // Fail-safe: red-flag đã ghi nhận không bị gỡ ở lượt sau.
  intake.symptom_codes = Array.from(new Set([...c.intake.symptom_codes, ...intake.symptom_codes]));
  const hadRedFlag = c.intake.symptom_codes.length > 0;

  const t0 = performance.now();
  const outcome = runNavigator(intake, message);
  assertNavigatorInvariants(outcome.reply);
  const reply: NavigatorReply = outcome.reply;

  c.intake = intake;
  c.messages.push({ role: "user", content: message ?? summarizeAnswers(answers), at });
  c.messages.push({ role: "assistant", content: reply.reply, at });
  c.last_reply = reply;
  c.updated_at = at;

  logRun(
    "navigator",
    row.owner_id,
    reply.trace_id,
    outcome.events,
    {
      red_flag: reply.red_flag.detected,
      next_action: reply.next_action,
      insufficient_evidence: reply.insufficient_evidence,
      guard_blocked: outcome.outOfScope,
    },
    Math.round(performance.now() - t0) + 140 + Math.round(Math.random() * 500),
    at,
  );

  if (row.owner_id && reply.red_flag.detected && !hadRedFlag) {
    addEvent(
      row.owner_id,
      "red_flag.detected",
      `Ghi nhận khi tư vấn: ${reply.red_flag.flags.map((f) => f.symptom.toLowerCase()).join(", ")}.`,
      { consultation_id: c.id, codes: reply.red_flag.flags.map((f) => f.code) },
      at,
    );
  }
}

function newConsultRow(ownerId: string | null, at: string = nowIso()): ConsultRow {
  const d = getDb();
  const profile = ownerId ? d.profiles[ownerId] : undefined;
  const row: ConsultRow = {
    token: randomToken(),
    owner_id: ownerId,
    consultation: {
      id: newId("c"),
      linked: Boolean(ownerId),
      intake: profile ? intakeFromProfile(profile) : emptyIntake(),
      messages: [],
      last_reply: null,
      created_at: at,
      updated_at: at,
    },
  };
  d.consultations.push(row);
  return row;
}

// ================================================================ brief helpers
function latestConsultIntake(patientId: string): IntakeProfile | null {
  const rows = getDb()
    .consultations.filter((c) => c.owner_id === patientId)
    .sort((a, b) => b.consultation.updated_at.localeCompare(a.consultation.updated_at));
  return rows[0]?.consultation.intake ?? null;
}

function briefFor(enc: EncounterOut): ReturnType<typeof buildBrief> {
  const d = getDb();
  const appt = d.appointments.find((a) => a.id === enc.appointment_id);
  return buildBrief({
    fullName: enc.patient_name,
    profile: d.profiles[enc.patient_id] ?? null,
    consultIntake: latestConsultIntake(enc.patient_id),
    events: eventsOf(enc.patient_id),
    reason: appt?.reason ?? null,
  });
}

function logBriefRun(enc: EncounterOut, at: string = nowIso()): void {
  const brief = enc.brief;
  if (!brief) return;
  const total = brief.trace_events.reduce((sum, e) => sum + (typeof e.ms === "number" ? e.ms : 0), 0);
  logRun("copilot", enc.patient_id, brief.trace_id, brief.trace_events, { red_flag: brief.red_flags.length > 0 }, total * 20 + 300, at);
}

const DIAGNOSIS_LANGUAGE = /(chẩn đoán xác định|bạn bị ung thư|đã mắc ung thư|ác tính|di căn)/i;

function validatePlan(plan: ScreeningPlan): void {
  if (!Array.isArray(plan.items)) fail(400, "Kế hoạch không hợp lệ.");
  plan.items.forEach((item, i) => {
    if (!item.sources?.length) fail(400, `Mục ${i + 1} của kế hoạch thiếu nguồn guideline.`);
    if (!Number.isFinite(item.interval_months) || item.interval_months < 1) {
      fail(400, `Mục ${i + 1}: chu kỳ (tháng) phải ≥ 1.`);
    }
    if (!item.method.trim()) fail(400, `Mục ${i + 1}: thiếu phương pháp.`);
    if (DIAGNOSIS_LANGUAGE.test(`${item.method} ${item.rationale}`) || DIAGNOSIS_LANGUAGE.test(plan.general_advice)) {
      fail(400, `Mục ${i + 1}: kế hoạch không được chứa ngôn ngữ chẩn đoán.`);
    }
    if (item.next_due && !/^\d{4}-\d{2}-\d{2}$/.test(item.next_due)) fail(400, `Mục ${i + 1}: ngày hẹn không hợp lệ.`);
  });
}

const planKey = (p: ScreeningPlan | null) =>
  JSON.stringify(
    p?.items.map((i) => [i.cancer_type, i.method, i.start_age, i.interval_months, i.next_due, i.rationale, i.priority]) ?? null,
  );

// ================================================================ seed
function seed(): MockDb {
  db = {
    version: DB_VERSION,
    users: [],
    profiles: {},
    consultations: [],
    appointments: [],
    encounters: [],
    editedEncounterIds: [],
    reminders: [],
    events: {},
    agentRuns: [],
  };
  const d = db;
  const today = todayISO();
  const mkUser = (id: string, email: string, full_name: string, role: UserOut["role"], createdOffset: number): MockUser => {
    const u: MockUser = { id, email, full_name, role, created_at: atDay(createdOffset, 8), password: MOCK_PASSWORD };
    d.users.push(u);
    return u;
  };
  const doctor = mkUser("u-doc", "doctor@demo.vn", "BS. Nguyễn Minh Anh", "doctor", -120);

  const patient = (
    id: string,
    email: string,
    name: string,
    dayOffset: number,
    messages: string[],
    service: string,
    preferredOffset: number,
  ): { user: MockUser; row: ConsultRow; appt: AppointmentOut } => {
    const user = mkUser(id, email, name, "patient", dayOffset);
    const at = atDay(dayOffset, 8);
    const row = newConsultRow(null, at);
    messages.forEach((m) => processTurn(row, { message: m }, at));
    addEvent(id, "account.created", "Tạo tài khoản từ phiên tư vấn trực tuyến.", { consultation_id: row.consultation.id }, at);
    linkConsultation(row, id, at);
    // gán lại owner cho agent run đã log trước khi gắn tài khoản
    d.agentRuns.forEach((r) => {
      if (r.patient_id === null && row.consultation.last_reply && r.agent === "navigator") r.patient_id = id;
    });
    const hint = row.consultation.last_reply?.booking_hint;
    const appt: AppointmentOut = {
      id: newId("a"),
      patient_id: id,
      patient_name: name,
      consultation_id: row.consultation.id,
      service_code: service,
      service_name: serviceName(service),
      preferred_date: addDaysISO(today, preferredOffset),
      scheduled_date: null,
      reason: hint?.reason ?? null,
      priority: hint?.priority === "urgent" || service === "oncology_priority" ? "urgent" : "routine",
      status: "requested",
      encounter_id: null,
      created_at: atDay(dayOffset, 9),
    };
    d.appointments.push(appt);
    addEvent(
      id,
      "appointment.requested",
      `Đặt lịch ${appt.service_name}, mong muốn ngày ${appt.preferred_date}.`,
      { appointment_id: appt.id, service_code: service, priority: appt.priority },
      atDay(dayOffset, 9),
    );
    return { user, row, appt };
  };

  // --- Lan: đã khám xong, có kế hoạch + nhắc lịch
  const lan = patient(
    "u-lan",
    "lan@demo.vn",
    "Trần Thị Lan",
    -42,
    ["Chào bạn, tôi là nữ, 45 tuổi.", "Mẹ tôi bị ung thư vú năm 60 tuổi. Tôi có cần chụp nhũ ảnh không?"],
    "breast_screening",
    -35,
  );
  d.profiles["u-lan"].genetics_history = ["breast_cancer_mother"];
  d.profiles["u-lan"].lifestyle = { smoking: false, alcohol: "none", exercise: "light", height_cm: 158, weight_kg: 55 };
  lan.appt.scheduled_date = addDaysISO(today, -35);
  lan.appt.status = "confirmed";
  addEvent("u-lan", "appointment.confirmed", `Lịch hẹn được xác nhận vào ngày ${lan.appt.scheduled_date}.`, { appointment_id: lan.appt.id }, atDay(-40, 10));
  const lanEnc: EncounterOut = {
    id: "e-lan-1",
    appointment_id: lan.appt.id,
    patient_id: "u-lan",
    patient_name: "Trần Thị Lan",
    doctor: publicUser(doctor),
    status: "in_progress",
    brief: null,
    draft_plan: null,
    final_plan: null,
    clinical_notes: null,
    conclusion: null,
    finalized_at: null,
    created_at: atDay(-35, 9),
    reminders: [],
    disclaimer: DISCLAIMER,
  };
  addEvent("u-lan", "encounter.started", "Bắt đầu khám tầm soát ung thư vú.", { encounter_id: lanEnc.id }, atDay(-35, 9));
  lanEnc.brief = briefFor(lanEnc);
  lanEnc.draft_plan = lanEnc.brief.draft_plan;
  d.encounters.push(lanEnc);
  logBriefRun(lanEnc, atDay(-35, 9));
  const draft = lanEnc.draft_plan;
  if (draft) {
    const items = draft.items.map((item) => {
      if (item.cancer_type === "breast") {
        return {
          ...item,
          interval_months: 12,
          next_due: addDaysISO(today, 330),
          rationale: "Phụ nữ 40–74 tuổi. Mẹ mắc ung thư vú: bác sĩ rút ngắn chu kỳ nhũ ảnh còn mỗi năm.",
          priority: 1,
        };
      }
      if (item.cancer_type === "cervical") return { ...item, next_due: addDaysISO(today, -2) };
      if (item.cancer_type === "colorectal") return { ...item, next_due: addDaysISO(today, 20) };
      return item;
    });
    lanEnc.final_plan = {
      ...draft,
      items,
      general_advice: "Duy trì vận động đều đặn, hạn chế rượu bia. Nếu sờ thấy khối bất thường, hãy đi khám sớm thay vì chờ lịch nhắc.",
    };
    d.editedEncounterIds.push(lanEnc.id);
  }
  lanEnc.status = "finalized";
  lanEnc.finalized_at = atDay(-35, 11);
  lanEnc.conclusion =
    "Khám vú lâm sàng hôm nay chưa ghi nhận dấu hiệu cần xử trí thêm. Vì mẹ bạn từng mắc ung thư vú, bạn nên chụp nhũ ảnh mỗi năm. Bạn cũng đến hạn xét nghiệm HPV cổ tử cung và nên làm xét nghiệm FIT hằng năm. Nếu có thay đổi bất thường ở vú, hãy đến khám sớm, không chờ lịch nhắc.";
  lanEnc.clinical_notes =
    "Khám vú 2 bên không sờ thấy khối. Tiền sử gia đình: mẹ ung thư vú phát hiện năm 60 tuổi. Chưa từng chụp nhũ ảnh. Rút ngắn chu kỳ nhũ ảnh còn 12 tháng.";
  lan.appt.status = "completed";
  lan.appt.encounter_id = lanEnc.id;
  lanEnc.final_plan?.items.forEach((item) => {
    if (!item.next_due) return;
    d.reminders.push({
      id: newId("r"),
      encounter_id: lanEnc.id,
      patient_id: "u-lan",
      cancer_type: item.cancer_type,
      method: item.method,
      due_date: item.next_due,
      status: item.next_due <= today ? "due" : "scheduled",
      completed_at: null,
      message: item.next_due <= today ? `Đã đến hạn ${item.method.toLowerCase()} theo kế hoạch bác sĩ đã duyệt.` : null,
    });
  });
  addEvent(
    "u-lan",
    "encounter.finalized",
    "Bác sĩ kết luận và duyệt kế hoạch tầm soát: ung thư vú, ung thư cổ tử cung, ung thư đại trực tràng.",
    { encounter_id: lanEnc.id, cancer_types: lanEnc.final_plan?.items.map((i) => i.cancer_type) ?? [] },
    atDay(-35, 11),
  );
  addEvent("u-lan", "reminder.due", "Đến hạn: Xét nghiệm HPV nguy cơ cao (ung thư cổ tử cung).", {}, atDay(-2, 7));

  // --- Tuấn: lịch đã xác nhận hôm nay (sẵn sàng "Bắt đầu khám")
  const tuan = patient(
    "u-tuan",
    "tuan@demo.vn",
    "Đỗ Quốc Tuấn",
    -7,
    ["Tôi 47 tuổi, nam, bị viêm gan B mạn đã nhiều năm. Có cần tầm soát ung thư gan không?"],
    "liver_screening",
    0,
  );
  tuan.appt.status = "confirmed";
  tuan.appt.scheduled_date = today;
  addEvent("u-tuan", "appointment.confirmed", `Lịch hẹn được xác nhận vào ngày ${today}.`, { appointment_id: tuan.appt.id }, atDay(-6, 10));

  // --- Minh: hút thuốc nhiều, chờ xác nhận
  patient(
    "u-minh",
    "minh@demo.vn",
    "Lê Văn Minh",
    -3,
    ["Tôi nam, 58 tuổi, hút thuốc khoảng 30 gói-năm, vẫn đang hút."],
    "lung_screening",
    3,
  );

  // --- Hoa: red-flag → lịch ưu tiên
  patient(
    "u-hoa",
    "hoa@demo.vn",
    "Phạm Thu Hoa",
    -1,
    ["Tôi nữ 52 tuổi.", "Hai tuần nay tôi sờ thấy một cục ở vú trái, không đau."],
    "oncology_priority",
    1,
  );

  // QA bệnh nhân mẫu cho observability
  const qa = patientPlanAnswer("Chụp nhũ ảnh mỗi năm có cần thiết không?", lanEnc.final_plan);
  logRun("patient_qa", "u-lan", qa.trace_id, [{ node: "answer", ms: 3, generator: "template", cited: qa.sources.length }], {}, 210, atDay(-30, 20));
  return d;
}

// ================================================================ health
export const health = () => respond(() => ({ status: "ok", agent: "mock" as const, db: "ok" }), 50);

// ================================================================ 1. Navigator
export const getNavigatorQuestionnaire = () => respond<Questionnaire>(() => NAVIGATOR_QUESTIONNAIRE, 150);

export const createConsultation = () =>
  respond<ConsultationCreated>(() => {
    const u = optionalUser();
    const row = newConsultRow(u?.role === "patient" ? u.id : null);
    return { access_token: row.token, consultation: row.consultation };
  }, 150);

export const getConsultation = (id: string, consultToken?: string | null) =>
  respond<ConsultationOut>(() => accessConsult(id, consultToken).consultation, 150);

export const sendConsultMessage = (id: string, body: NavigatorMessageIn, consultToken?: string | null) =>
  respond<ConsultationOut>(() => {
    const row = accessConsult(id, consultToken);
    const message = body.message?.trim();
    if (!message && !body.answers?.length) fail(400, "Cần gửi tin nhắn hoặc câu trả lời bảng hỏi.");
    if (message && message.length > 2000) fail(400, "Tin nhắn tối đa 2000 ký tự.");
    const turns = row.consultation.messages.filter((m) => m.role === "user").length;
    if (turns >= MAX_CONSULT_TURNS) fail(429, "Phiên tư vấn đã đạt giới hạn 40 lượt. Hãy bắt đầu cuộc trò chuyện mới.");
    processTurn(row, body);
    return row.consultation;
  }, 700);

export const claimConsultation = (id: string, consultToken: string) =>
  respond<ConsultationOut>(() => {
    const u = requirePatient();
    const row = getDb().consultations.find((c) => c.consultation.id === id) ?? fail(404, "Không tìm thấy phiên tư vấn.");
    if (row.owner_id === u.id) return row.consultation;
    if (row.owner_id || row.token !== consultToken) fail(401, "Mã truy cập phiên tư vấn không hợp lệ.");
    linkConsultation(row, u.id);
    return row.consultation;
  });

export const listServices = () => respond<ServiceOut[]>(() => SERVICES, 120);

export const listEducationTopics = () =>
  respond<Array<{ cancer_type: CancerType; title: string }>>(
    () => EDUCATION.map((e) => ({ cancer_type: e.cancer_type, title: e.title })),
    120,
  );

export const getEducation = (type: CancerType) =>
  respond<EducationContent>(
    () => EDUCATION.find((e) => e.cancer_type === type) ?? fail(404, "Chưa có tài liệu cho chủ đề này."),
    150,
  );

// ================================================================ 2. Auth
export const register = (b: RegisterIn) =>
  respond<UserOut>(() => {
    const d = getDb();
    if (b.role !== "patient") fail(403, "Chỉ được đăng ký tài khoản bệnh nhân.");
    const email = b.email.trim().toLowerCase();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) fail(400, "Email không hợp lệ.");
    if (!b.password || b.password.length < 6) fail(400, "Mật khẩu tối thiểu 6 ký tự.");
    if (!b.full_name.trim()) fail(400, "Vui lòng nhập họ tên.");
    if (d.users.some((u) => u.email === email)) fail(400, "Email đã được đăng ký. Hãy đăng nhập.");
    let row: ConsultRow | null = null;
    if (b.consultation_id) {
      row = d.consultations.find((c) => c.consultation.id === b.consultation_id) ?? null;
      if (!row || row.owner_id || row.token !== b.consultation_token) {
        fail(400, "Phiên tư vấn không hợp lệ hoặc đã được gắn vào tài khoản khác.");
      }
    }
    const user: MockUser = {
      id: newId("u"),
      email,
      full_name: b.full_name.trim(),
      role: "patient",
      created_at: nowIso(),
      password: b.password,
    };
    d.users.push(user);
    addEvent(user.id, "account.created", row ? "Tạo tài khoản từ phiên tư vấn trực tuyến." : "Tạo tài khoản bệnh nhân.", {
      consultation_id: row?.consultation.id ?? null,
    });
    if (row) linkConsultation(row, user.id);
    return publicUser(user);
  }, 400);

export const login = (b: LoginIn) =>
  respond<TokenOut>(() => {
    const email = b.email.trim().toLowerCase();
    const user = getDb().users.find((u) => u.email === email);
    if (!user || user.password !== b.password) return fail(401, "Email hoặc mật khẩu không đúng.");
    return { access_token: `mock-token:${user.id}`, token_type: "bearer", user: publicUser(user) };
  }, 350);

export const me = () => respond<UserOut>(() => publicUser(requireUser()));

// ================================================================ 3. Bệnh nhân
export const getProfile = () =>
  respond<PatientProfileOut>(() => {
    const u = requirePatient();
    return getDb().profiles[u.id] ?? fail(404, "Chưa có hồ sơ sức khoẻ.");
  });

export const putProfile = (b: PatientProfileIn) =>
  respond<PatientProfileOut>(() => {
    const u = requirePatient();
    if (!Number.isFinite(b.age) || b.age < 0 || b.age > 120) fail(400, "Tuổi không hợp lệ.");
    const profile: PatientProfileOut = { ...b, user_id: u.id, lifestyle_score: null, updated_at: nowIso() };
    getDb().profiles[u.id] = profile;
    addEvent(u.id, "profile.updated", `Cập nhật hồ sơ: ${b.age} tuổi, ${b.gender === "female" ? "nữ" : b.gender === "male" ? "nam" : "giới tính khác"}.`);
    return profile;
  });

export const getMyRecord = () => respond<PatientRecordOut>(() => recordFor(requirePatient().id, "patient"));

export const createAppointment = (b: AppointmentIn) =>
  respond<AppointmentOut>(() => {
    const u = requirePatient();
    const d = getDb();
    const service = SERVICES.find((s) => s.code === b.service_code) ?? fail(400, "Dịch vụ không tồn tại.");
    if (!/^\d{4}-\d{2}-\d{2}$/.test(b.preferred_date) || b.preferred_date < todayISO()) {
      fail(400, "Ngày mong muốn phải từ hôm nay trở đi.");
    }
    const open = d.appointments.filter((a) => a.patient_id === u.id && (a.status === "requested" || a.status === "confirmed"));
    if (open.length >= 3) fail(409, "Bạn đang có 3 lịch hẹn chưa hoàn tất. Hãy huỷ bớt hoặc chờ khám xong trước khi đặt thêm.");
    let urgent = service.code === "oncology_priority";
    if (b.consultation_id) {
      const row = d.consultations.find((c) => c.consultation.id === b.consultation_id && c.owner_id === u.id);
      if (!row) fail(400, "Phiên tư vấn không thuộc tài khoản của bạn.");
      if (row?.consultation.last_reply?.red_flag.detected || row?.consultation.intake.symptom_codes.length) urgent = true;
    }
    const appt: AppointmentOut = {
      id: newId("a"),
      patient_id: u.id,
      patient_name: u.full_name,
      consultation_id: b.consultation_id ?? null,
      service_code: service.code,
      service_name: service.name,
      preferred_date: b.preferred_date,
      scheduled_date: null,
      reason: b.reason?.trim() || null,
      priority: urgent ? "urgent" : "routine",
      status: "requested",
      encounter_id: null,
      created_at: nowIso(),
    };
    d.appointments.push(appt);
    addEvent(u.id, "appointment.requested", `Đặt lịch ${service.name}, mong muốn ngày ${b.preferred_date}.`, {
      appointment_id: appt.id,
      service_code: service.code,
      priority: appt.priority,
    });
    return appt;
  }, 400);

export const listMyAppointments = () =>
  respond<AppointmentOut[]>(() => {
    const u = requirePatient();
    return getDb()
      .appointments.filter((a) => a.patient_id === u.id)
      .sort((a, b) => b.created_at.localeCompare(a.created_at));
  });

export const cancelAppointment = (id: string) =>
  respond<AppointmentOut>(() => {
    const u = requirePatient();
    const appt = getDb().appointments.find((a) => a.id === id && a.patient_id === u.id) ?? fail(404, "Không tìm thấy lịch hẹn.");
    if (appt.status === "completed" || appt.status === "cancelled") fail(409, "Lịch hẹn đã hoàn tất hoặc đã huỷ.");
    if (appt.encounter_id) fail(409, "Lịch hẹn đã bắt đầu khám nên không thể huỷ.");
    appt.status = "cancelled";
    addEvent(u.id, "appointment.cancelled", `Huỷ lịch ${appt.service_name}.`, { appointment_id: appt.id });
    return appt;
  });

export const getEncounter = (id: string) =>
  respond<EncounterOut>(() => {
    const u = requirePatient();
    refreshReminders();
    const enc = getDb().encounters.find((e) => e.id === id && e.patient_id === u.id) ?? fail(404, "Không tìm thấy lượt khám.");
    return patientView(encounterWithReminders(enc));
  });

export const askEncounterQuestion = (id: string, question: string) =>
  respond<QuestionAnswer>(() => {
    const u = requirePatient();
    const enc = getDb().encounters.find((e) => e.id === id && e.patient_id === u.id) ?? fail(404, "Không tìm thấy lượt khám.");
    if (enc.status !== "finalized") fail(409, "Bác sĩ chưa hoàn tất lượt khám này.");
    const q = question.trim();
    if (q.length < 1 || q.length > 1000) fail(400, "Câu hỏi cần từ 1 đến 1000 ký tự.");
    const answer = patientPlanAnswer(q, enc.final_plan);
    logRun("patient_qa", u.id, answer.trace_id, [{ node: "answer", ms: 3, generator: "template", cited: answer.sources.length }], {
      insufficient_evidence: answer.insufficient_evidence,
    });
    return answer;
  }, 600);

export const listReminders = (status?: ReminderStatus) =>
  respond<ReminderOut[]>(() => {
    const u = requirePatient();
    refreshReminders();
    return getDb()
      .reminders.filter((r) => r.patient_id === u.id && (!status || r.status === status))
      .sort((a, b) => a.due_date.localeCompare(b.due_date));
  });

export const completeReminder = (id: string, completedAt?: string) =>
  respond<ReminderOut>(() => {
    const u = requirePatient();
    const d = getDb();
    const r = d.reminders.find((x) => x.id === id && x.patient_id === u.id) ?? fail(404, "Không tìm thấy lịch nhắc.");
    if (r.status === "done") return r;
    r.status = "done";
    r.completed_at = completedAt ?? todayISO();
    addEvent(u.id, "reminder.done", `Đã thực hiện ${r.method} (${LABEL_VI[r.cancer_type]}).`, {
      reminder_id: r.id,
      cancer_types: [r.cancer_type],
    });
    // Chu kỳ kế tiếp theo interval_months của kế hoạch đã duyệt (không tạo trùng)
    const enc = d.encounters.find((e) => e.id === r.encounter_id);
    const item = enc?.final_plan?.items.find((i) => i.cancer_type === r.cancer_type && i.method === r.method);
    if (item && item.interval_months > 0) {
      const base = parseISODate(r.completed_at);
      base.setMonth(base.getMonth() + item.interval_months);
      const due = `${base.getFullYear()}-${String(base.getMonth() + 1).padStart(2, "0")}-${String(base.getDate()).padStart(2, "0")}`;
      const exists = d.reminders.some(
        (x) => x.encounter_id === r.encounter_id && x.method === r.method && x.due_date === due && x.status !== "done",
      );
      if (!exists) {
        d.reminders.push({ ...r, id: newId("r"), due_date: due, status: "scheduled", completed_at: null, message: null });
      }
    }
    return r;
  });

// ================================================================ 4. Bác sĩ
const sortQueue = (a: AppointmentOut, b: AppointmentOut) => {
  if (a.priority !== b.priority) return a.priority === "urgent" ? -1 : 1;
  const da = a.scheduled_date ?? a.preferred_date;
  const dbb = b.scheduled_date ?? b.preferred_date;
  return da.localeCompare(dbb) || a.created_at.localeCompare(b.created_at);
};

function paginate<T>(items: T[], page: number): Page<T> {
  const p = Math.max(1, Math.floor(page) || 1);
  return { items: items.slice((p - 1) * PAGE_SIZE, p * PAGE_SIZE), total: items.length, page: p, page_size: PAGE_SIZE };
}

export const listDoctorAppointments = (status?: AppointmentStatus, page = 1) =>
  respond<Page<AppointmentOut>>(() => {
    requireDoctor();
    const items = getDb()
      .appointments.filter((a) => !status || a.status === status)
      .sort(sortQueue);
    return paginate(items, page);
  });

export const confirmAppointment = (id: string, b: ConfirmAppointmentIn) =>
  respond<AppointmentOut>(() => {
    requireDoctor();
    const appt = getDb().appointments.find((a) => a.id === id) ?? fail(404, "Không tìm thấy lịch hẹn.");
    if (appt.status !== "requested") fail(409, "Chỉ xác nhận được lịch đang chờ.");
    if (!/^\d{4}-\d{2}-\d{2}$/.test(b.scheduled_date)) fail(400, "Ngày hẹn không hợp lệ.");
    appt.status = "confirmed";
    appt.scheduled_date = b.scheduled_date;
    addEvent(appt.patient_id, "appointment.confirmed", `Lịch hẹn được xác nhận vào ngày ${b.scheduled_date}.`, {
      appointment_id: appt.id,
    });
    return appt;
  });

export const startAppointment = (id: string) =>
  respond<EncounterOut>(() => {
    const doc = requireDoctor();
    const d = getDb();
    const appt = d.appointments.find((a) => a.id === id) ?? fail(404, "Không tìm thấy lịch hẹn.");
    if (appt.encounter_id) {
      const existing = d.encounters.find((e) => e.id === appt.encounter_id);
      if (existing) return encounterWithReminders(existing);
    }
    if (appt.status === "cancelled" || appt.status === "completed") fail(409, "Lịch hẹn đã huỷ hoặc đã hoàn tất.");
    const enc: EncounterOut = {
      id: newId("e"),
      appointment_id: appt.id,
      patient_id: appt.patient_id,
      patient_name: appt.patient_name,
      doctor: publicUser(doc),
      status: "in_progress",
      brief: null,
      draft_plan: null,
      final_plan: null,
      clinical_notes: null,
      conclusion: null,
      finalized_at: null,
      created_at: nowIso(),
      reminders: [],
      disclaimer: DISCLAIMER,
    };
    addEvent(appt.patient_id, "encounter.started", `Bắt đầu khám: ${appt.service_name}.`, { encounter_id: enc.id });
    enc.brief = briefFor(enc);
    enc.draft_plan = enc.brief.draft_plan;
    appt.encounter_id = enc.id;
    d.encounters.push(enc);
    logBriefRun(enc);
    return enc;
  }, 900);

export const listPatients = (q?: string) =>
  respond<PatientListItem[]>(() => {
    requireDoctor();
    const d = getDb();
    const needle = q?.trim().toLowerCase();
    return d.users
      .filter((u) => u.role === "patient")
      .filter((u) => !needle || u.full_name.toLowerCase().includes(needle) || u.email.includes(needle))
      .map((u) => {
        const events = eventsOf(u.id);
        return {
          user: publicUser(u),
          profile: d.profiles[u.id] ?? null,
          open_appointments: d.appointments.filter(
            (a) => a.patient_id === u.id && (a.status === "requested" || a.status === "confirmed"),
          ).length,
          last_activity: events.length ? events[events.length - 1].at : null,
        };
      })
      .sort((a, b) => (b.last_activity ?? "").localeCompare(a.last_activity ?? ""));
  });

export const getPatientRecord = (id: string) =>
  respond<PatientRecordOut>(() => {
    requireDoctor();
    return recordFor(id, "doctor");
  });

export const getDoctorEncounter = (id: string) =>
  respond<EncounterOut>(() => {
    requireDoctor();
    refreshReminders();
    const enc = getDb().encounters.find((e) => e.id === id) ?? fail(404, "Không tìm thấy lượt khám.");
    return encounterWithReminders(enc);
  });

export const regenerateBrief = (id: string) =>
  respond<EncounterOut>(() => {
    requireDoctor();
    const enc = getDb().encounters.find((e) => e.id === id) ?? fail(404, "Không tìm thấy lượt khám.");
    if (enc.status === "finalized") fail(409, "Lượt khám đã hoàn tất, không thể tạo lại brief.");
    enc.brief = briefFor(enc);
    enc.draft_plan = enc.brief.draft_plan;
    logBriefRun(enc);
    return encounterWithReminders(enc);
  }, 900);

export const askCopilot = (id: string, b: CopilotAskIn) =>
  respond<QuestionAnswer>(() => {
    requireDoctor();
    const enc = getDb().encounters.find((e) => e.id === id) ?? fail(404, "Không tìm thấy lượt khám.");
    if (!b.question.trim()) fail(400, "Câu hỏi không được để trống.");
    if (b.history.length > 8) fail(400, "Lịch sử hội thoại tối đa 8 lượt.");
    const answer = copilotAnswer(b.question, enc.brief, eventsOf(enc.patient_id));
    logRun("copilot_qa", enc.patient_id, answer.trace_id, answer.trace_events, {
      insufficient_evidence: answer.insufficient_evidence,
      guard_blocked: answer.trace_events.some((e) => e.blocked === true),
    });
    return answer;
  }, 700);

export const finalizeEncounter = (id: string, b: FinalizeEncounterIn) =>
  respond<EncounterOut>(() => {
    const doc = requireDoctor();
    const d = getDb();
    const enc = d.encounters.find((e) => e.id === id) ?? fail(404, "Không tìm thấy lượt khám.");
    if (enc.status === "finalized") fail(409, "Lượt khám đã được hoàn tất.");
    const conclusion = b.conclusion?.trim();
    if (!conclusion) fail(400, "Kết luận gửi bệnh nhân là bắt buộc.");
    let plan: ScreeningPlan | null;
    if (b.final_plan !== undefined) plan = b.final_plan;
    else if (b.use_draft === false) plan = null;
    else plan = enc.draft_plan;
    if (plan) {
      validatePlan(plan);
      if (plan.items.length === 0) plan = null;
    }
    if (plan && planKey(plan) !== planKey(enc.draft_plan)) d.editedEncounterIds.push(enc.id);
    if (!plan && enc.draft_plan) d.editedEncounterIds.push(enc.id);

    enc.status = "finalized";
    enc.final_plan = plan ? clone(plan) : null;
    enc.conclusion = conclusion ?? null;
    enc.clinical_notes = b.clinical_notes?.trim() || null;
    enc.finalized_at = nowIso();
    enc.doctor = publicUser(doc);
    plan?.items.forEach((item) => {
      if (!item.next_due) return;
      d.reminders.push({
        id: newId("r"),
        encounter_id: enc.id,
        patient_id: enc.patient_id,
        cancer_type: item.cancer_type,
        method: item.method,
        due_date: item.next_due,
        status: "scheduled",
        completed_at: null,
        message: null,
      });
    });
    const appt = d.appointments.find((a) => a.id === enc.appointment_id);
    if (appt) appt.status = "completed";
    const types = plan?.items.map((i) => i.cancer_type) ?? [];
    addEvent(
      enc.patient_id,
      "encounter.finalized",
      types.length
        ? `Bác sĩ kết luận và duyệt kế hoạch tầm soát: ${Array.from(new Set(types)).map((t) => LABEL_VI[t]).join(", ")}.`
        : "Bác sĩ kết luận lượt khám (không lập kế hoạch tầm soát định kỳ).",
      { encounter_id: enc.id, cancer_types: types },
    );
    refreshReminders();
    return encounterWithReminders(enc);
  }, 600);

function quantile(sorted: number[], q: number): number {
  if (!sorted.length) return 0;
  const idx = Math.min(sorted.length - 1, Math.max(0, Math.ceil(q * sorted.length) - 1));
  return sorted[idx];
}

export const getMetrics = () =>
  respond<MetricsOut>(() => {
    requireDoctor();
    const d = getDb();
    const runs = d.agentRuns;
    const latencies = runs.map((r) => r.latency_ms).sort((a, b) => a - b);
    const byStatus: Record<string, number> = { requested: 0, confirmed: 0, completed: 0, cancelled: 0 };
    d.appointments.forEach((a) => {
      byStatus[a.status] = (byStatus[a.status] ?? 0) + 1;
    });
    const consults = d.consultations.map((c) => c.consultation);
    return {
      consultations: consults.length,
      linked_consultations: consults.filter((c) => c.linked).length,
      red_flag_consultations: consults.filter((c) => c.intake.symptom_codes.length > 0 || c.last_reply?.red_flag.detected)
        .length,
      booking_suggested: consults.filter(
        (c) => c.last_reply?.next_action === "suggest_booking" || c.last_reply?.next_action === "urgent_care",
      ).length,
      appointments_by_status: byStatus,
      encounters_finalized: d.encounters.filter((e) => e.status === "finalized").length,
      plans_edited_by_doctor: new Set(d.editedEncounterIds).size,
      agent_runs: runs.length,
      agent_fallback_rate: runs.length ? runs.filter((r) => r.generator === "template_fallback").length / runs.length : 0,
      agent_insufficient_rate: runs.length ? runs.filter((r) => r.insufficient_evidence).length / runs.length : 0,
      agent_latency_ms_p50: quantile(latencies, 0.5),
      agent_latency_ms_p95: quantile(latencies, 0.95),
    };
  });

export const listAgentRuns = (agent?: AgentName, page = 1) =>
  respond<Page<AgentRunOut>>(() => {
    requireDoctor();
    const items = getDb()
      .agentRuns.filter((r) => !agent || r.agent === agent)
      .sort((a, b) => b.created_at.localeCompare(a.created_at));
    return paginate(items, page);
  });

export const listDueReminders = () =>
  respond<ReminderOut[]>(() => {
    requireDoctor();
    refreshReminders();
    return getDb()
      .reminders.filter((r) => r.status === "due")
      .sort((a, b) => a.due_date.localeCompare(b.due_date));
  });
