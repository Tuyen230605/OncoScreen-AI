/**
 * Logic rule-based cho chế độ mock — mô phỏng ai_core (intake → red-flag → eligibility → triage; Copilot brief).
 * Bất biến được đảm bảo ở đây (và kiểm tra lại bằng assertNavigatorInvariants / assertBriefInvariants):
 * - red-flag ⇒ next_action = urgent_care, không có suggestion, có booking_hint ưu tiên.
 * - suggest_booking | urgent_care ⇒ có booking_hint.
 * - mọi ScreeningSuggestion / PlanItem có ≥ 1 nguồn.
 * Không có nội dung chẩn đoán: chỉ đối chiếu luật guideline và chuyển bác sĩ.
 */
import type {
  Answer,
  BookingHint,
  BriefFact,
  CancerType,
  ClinicalBrief,
  Gender,
  IntakeProfile,
  NavigatorReply,
  NextAction,
  PatientProfileOut,
  PlanItem,
  QuestionAnswer,
  RecordEventOut,
  RedFlag,
  RedFlagResult,
  RiskFactor,
  RiskLevel,
  ScreeningPlan,
  ScreeningSuggestion,
  Source,
  TraceEvent,
} from "@/types/api";
import {
  COPILOT_DISCLAIMER,
  DISCLAIMER,
  FAQ,
  GUIDELINE_SOURCES,
  LABEL_VI,
  MOCK_MODEL,
  RED_FLAG_DEFS,
  RED_FLAG_MESSAGE,
  SCREENING_RULES,
  SERVICES,
  type ScreeningRule,
} from "./fixtures";

// ---------------------------------------------------------------- tiện ích
export function fold(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase();
}

export function newId(prefix: string): string {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

export function newTraceId(): string {
  let out = "";
  for (let i = 0; i < 16; i++) out += Math.floor(Math.random() * 16).toString(16);
  return out;
}

const uniq = <T,>(xs: T[]): T[] => Array.from(new Set(xs));

function uniqSources(sources: Source[]): Source[] {
  const seen = new Set<string>();
  return sources.filter((s) => {
    const key = `${s.doc_id}|${s.section ?? ""}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function emptyIntake(): IntakeProfile {
  return {
    age: null,
    gender: null,
    family_history: [],
    personal_cancer_history: null,
    smoking: null,
    pack_years: null,
    hepatitis_b_or_c: null,
    cirrhosis: null,
    hpv_vaccinated: null,
    symptom_codes: [],
  };
}

const cloneIntake = (i: IntakeProfile): IntakeProfile => ({
  ...i,
  family_history: [...i.family_history],
  symptom_codes: [...i.symptom_codes],
});

function asBool(v: unknown): boolean | null {
  if (typeof v === "boolean") return v;
  if (typeof v === "number") return v === 1;
  if (typeof v === "string") {
    const s = v.trim().toLowerCase();
    if (["true", "yes", "có", "co", "1"].includes(s)) return true;
    if (["false", "no", "không", "khong", "0"].includes(s)) return false;
  }
  return null;
}

function asNum(v: unknown): number | null {
  if (v === null || v === undefined || v === "") return null;
  const n = Number(String(v).replace(",", "."));
  return Number.isFinite(n) ? n : null;
}

const LABEL_TO_CANCER: Record<string, CancerType> = {
  "ung thư vú": "breast",
  "ung thư cổ tử cung": "cervical",
  "ung thư đại trực tràng": "colorectal",
  "ung thư gan": "liver",
  "ung thư phổi": "lung",
  "ung thư tuyến tiền liệt": "prostate",
  khác: "other",
};

const GENDER_FROM_LABEL: Record<string, Gender> = { nữ: "female", nam: "male", khác: "other" };

// ---------------------------------------------------------------- intake
export function intakeFromAnswers(intake: IntakeProfile, answers: Answer[]): IntakeProfile {
  let next = cloneIntake(intake);
  for (const a of answers) {
    const v = a.value;
    switch (a.question_id) {
      case "age": {
        const n = asNum(v);
        if (n !== null && n >= 0 && n <= 120) next.age = Math.floor(n);
        break;
      }
      case "gender":
        if (typeof v === "string" && GENDER_FROM_LABEL[v.trim().toLowerCase()]) {
          next.gender = GENDER_FROM_LABEL[v.trim().toLowerCase()];
        }
        break;
      case "family_history": {
        const values = Array.isArray(v) ? v : [v];
        next.family_history = uniq(
          values
            .map((x) => (typeof x === "string" ? LABEL_TO_CANCER[x.trim().toLowerCase()] : undefined))
            .filter((x): x is CancerType => Boolean(x)),
        );
        break;
      }
      case "personal_cancer_history":
        next.personal_cancer_history = asBool(v) ?? next.personal_cancer_history;
        break;
      case "smoking": {
        const b = asBool(v);
        if (b !== null) {
          next.smoking = b;
          if (!b) next.pack_years = null;
        }
        break;
      }
      case "pack_years": {
        const n = asNum(v);
        if (n !== null && n >= 0) next.pack_years = n;
        break;
      }
      case "hbv_hcv":
        next.hepatitis_b_or_c = asBool(v) ?? next.hepatitis_b_or_c;
        break;
      case "cirrhosis":
        next.cirrhosis = asBool(v) ?? next.cirrhosis;
        break;
      case "hpv_vaccine":
        next.hpv_vaccinated = asBool(v) ?? next.hpv_vaccinated;
        break;
      case "other_symptoms":
        if (typeof v === "string" && v.trim()) next = intakeFromText(next, v);
        break;
      default:
        if (a.question_id.startsWith("symptom_") && asBool(v) === true) {
          next.symptom_codes = uniq([...next.symptom_codes, a.question_id]);
        }
    }
  }
  return next;
}

// So khớp trên chữ CÓ dấu (bỏ dấu sẽ nhầm "cô"/"có", "dì"/"đi", "bà"/"ba"…).
const RELATIVE =
  /(?<!\p{L})(bố|mẹ|cha|bà ngoại|bà nội|ông ngoại|ông nội|ông|bà|cô|dì|chú|bác|cậu|mợ|anh trai|chị gái|em gái|em trai|anh chị em|chị ruột|anh ruột|con trai|con gái|người thân|gia đình|họ hàng|chị)(?!\p{L})/u;
const CANCER_WORDS: Array<[RegExp, CancerType]> = [
  [/ung thu vu/, "breast"],
  [/ung thu co tu cung/, "cervical"],
  [/ung thu (dai truc trang|dai trang|truc trang|ruot)/, "colorectal"],
  [/ung thu gan/, "liver"],
  [/ung thu phoi/, "lung"],
  [/ung thu tuyen tien liet/, "prostate"],
];
const FEMALE = /(?<!\p{L})(nữ|phụ nữ|nữ giới)(?!\p{L})/u;
const MALE = /(?<!\p{L})(?<!việt )(?<!miền )(nam|nam giới|đàn ông)(?!\p{L})/u;

function negatedAt(sentence: string, index: number): boolean {
  const before = sentence.slice(Math.max(0, index - 16), index);
  return /\b(khong|chua|chang)\b/.test(before);
}

function firstMatch(sentence: string, re: RegExp): RegExpExecArray | null {
  return re.exec(sentence);
}

export function symptomCodesFromText(text: string): string[] {
  const codes: string[] = [];
  for (const sentence of fold(text).split(/[.!?;\n]+/)) {
    for (const def of RED_FLAG_DEFS) {
      for (const pattern of def.patterns) {
        const m = firstMatch(sentence, pattern);
        if (m && !negatedAt(sentence, m.index)) {
          codes.push(def.code);
          break;
        }
      }
    }
  }
  return uniq(codes);
}

export function intakeFromText(intake: IntakeProfile, text: string): IntakeProfile {
  const next = cloneIntake(intake);
  // Tách theo mệnh đề để "Tôi nữ, 45 tuổi, mẹ tôi bị ung thư vú" không gán tuổi/giới của người thân cho người dùng.
  const clauses = text.normalize("NFC").toLowerCase().split(/[.,!?;\n]+/);
  clauses.forEach((original) => {
    const s = fold(original);
    const hasRelative = RELATIVE.test(original);
    if (!hasRelative) {
      const age = /(\d{1,3})\s*tuoi/.exec(s);
      if (age) {
        const n = Number(age[1]);
        if (n > 0 && n <= 120) next.age = n;
      }
      const born = /sinh (nam )?(19\d\d|20\d\d)/.exec(s);
      if (born) next.age = new Date().getFullYear() - Number(born[2]);
      if (FEMALE.test(original)) next.gender = "female";
      else if (MALE.test(original)) next.gender = "male";
    }

    const selfCancer = /\b(toi|minh|tui)\b.*\b(bi|mac|dieu tri) ung thu/.exec(s);
    if (hasRelative && /ung thu/.test(s)) {
      const types = CANCER_WORDS.filter(([re]) => re.test(s)).map(([, t]) => t);
      next.family_history = uniq([...next.family_history, ...(types.length ? types : (["other"] as CancerType[]))]);
    } else if (selfCancer) {
      next.personal_cancer_history = !/\b(chua|khong)\b/.test(s.slice(0, selfCancer.index + selfCancer[0].length));
    }

    const smoke = /hut thuoc/.exec(s);
    if (smoke) next.smoking = !/(khong|chua bao gio|chua tung|chua) hut thuoc/.test(s);
    const packYears = /(\d+(?:[.,]\d+)?)\s*goi[\s-]*nam/.exec(s);
    if (packYears) {
      next.pack_years = Number(packYears[1].replace(",", "."));
      next.smoking = true;
    } else {
      const perDay = /(\d+(?:[.,]\d+)?)\s*goi\s*(?:\/|moi|mot|1)?\s*ngay\D{0,20}?(\d+)\s*nam/.exec(s);
      if (perDay) {
        next.pack_years = Number(perDay[1].replace(",", ".")) * Number(perDay[2]);
        next.smoking = true;
      }
    }
    const hep = /viem gan (b|c)\b/.exec(s);
    if (hep) next.hepatitis_b_or_c = !negatedAt(s, hep.index);
    const cir = /xo gan/.exec(s);
    if (cir) next.cirrhosis = !negatedAt(s, cir.index);
    const hpv = /(tiem|chich)\D{0,20}hpv/.exec(s);
    if (hpv) next.hpv_vaccinated = !negatedAt(s, hpv.index + 1) && !/chua (tiem|chich)/.test(s);
  });
  next.symptom_codes = uniq([...next.symptom_codes, ...symptomCodesFromText(text)]);
  return next;
}

/** Hồ sơ tài khoản → intake (genetics_history dạng "<cancer>_cancer_<người thân>"). */
export function intakeFromProfile(profile: PatientProfileOut): IntakeProfile {
  const types = profile.genetics_history
    .map((code) => code.split("_cancer_")[0])
    .filter((t): t is CancerType => t in LABEL_VI);
  const ls = profile.lifestyle;
  return {
    ...emptyIntake(),
    age: profile.age,
    gender: profile.gender,
    family_history: uniq(types),
    smoking: typeof ls.smoking === "boolean" ? ls.smoking : null,
    pack_years: typeof ls.pack_years === "number" ? ls.pack_years : null,
    hepatitis_b_or_c: typeof ls.hepatitis_b_or_c === "boolean" ? ls.hepatitis_b_or_c : null,
    cirrhosis: typeof ls.cirrhosis === "boolean" ? ls.cirrhosis : null,
  };
}

/** Gộp: giá trị của `primary` thắng; danh sách cộng dồn. */
export function mergeIntake(primary: IntakeProfile | null, secondary: IntakeProfile | null): IntakeProfile {
  const a = primary ?? emptyIntake();
  const b = secondary ?? emptyIntake();
  return {
    age: a.age ?? b.age,
    gender: a.gender ?? b.gender,
    family_history: uniq([...a.family_history, ...b.family_history]),
    personal_cancer_history: a.personal_cancer_history ?? b.personal_cancer_history,
    smoking: a.smoking ?? b.smoking,
    pack_years: a.pack_years ?? b.pack_years,
    hepatitis_b_or_c: a.hepatitis_b_or_c ?? b.hepatitis_b_or_c,
    cirrhosis: a.cirrhosis ?? b.cirrhosis,
    hpv_vaccinated: a.hpv_vaccinated ?? b.hpv_vaccinated,
    symptom_codes: uniq([...a.symptom_codes, ...b.symptom_codes]),
  };
}

export function missingInfo(intake: IntakeProfile): string[] {
  const missing: string[] = [];
  if (intake.age === null) missing.push("age");
  if (intake.gender === null) missing.push("gender");
  if (intake.smoking && intake.pack_years === null) missing.push("pack_years");
  return missing;
}

// ---------------------------------------------------------------- red-flag
export function redFlagFor(codes: string[]): RedFlagResult {
  const flags: RedFlag[] = RED_FLAG_DEFS.filter((d) => codes.includes(d.code)).map((d) => ({
    code: d.code,
    symptom: d.symptom,
    severity: d.severity,
    advice: d.advice,
  }));
  return flags.length
    ? { detected: true, flags, message: RED_FLAG_MESSAGE }
    : { detected: false, flags: [], message: null };
}

// ---------------------------------------------------------------- eligibility
function requirementMet(req: ScreeningRule["requires"][number], intake: IntakeProfile): boolean {
  if (req === "pack_years>=20") return Boolean(intake.smoking) && (intake.pack_years ?? 0) >= 20;
  if (req === "cirrhosis") return Boolean(intake.cirrhosis);
  return Boolean(intake.hepatitis_b_or_c) && !intake.cirrhosis;
}

export function evaluate(intake: IntakeProfile): {
  evaluated: boolean;
  suggestions: ScreeningSuggestion[];
  risk_factors: RiskFactor[];
} {
  if (intake.age === null || intake.gender === null) return { evaluated: false, suggestions: [], risk_factors: [] };
  const order: RiskLevel[] = ["average", "elevated", "high"];
  const risk = new Map<CancerType, RiskFactor>();
  const addRisk = (cancer_type: CancerType, level: RiskLevel, reason: string) => {
    const current = risk.get(cancer_type);
    if (!current) {
      risk.set(cancer_type, { cancer_type, level, reasons: [reason] });
      return;
    }
    current.reasons.push(reason);
    if (order.indexOf(level) > order.indexOf(current.level)) current.level = level;
  };
  intake.family_history.forEach((t) => {
    if (t !== "other") addRisk(t, "elevated", `Có người thân mắc ${LABEL_VI[t]}`);
  });
  if (intake.smoking && (intake.pack_years ?? 0) >= 20) addRisk("lung", "high", `Hút thuốc ${intake.pack_years} gói-năm`);
  if (intake.hepatitis_b_or_c) addRisk("liver", "high", "Viêm gan B/C mạn tính");
  if (intake.cirrhosis) addRisk("liver", "high", "Xơ gan");

  const risk_factors = Array.from(risk.values());
  if (intake.personal_cancer_history) return { evaluated: true, suggestions: [], risk_factors };

  const age = intake.age;
  const gender = intake.gender;
  const suggestions = SCREENING_RULES.filter(
    (r) =>
      (r.gender === "any" || r.gender === gender) &&
      age >= r.min_age &&
      (r.max_age === null || age <= r.max_age) &&
      r.requires.every((req) => requirementMet(req, intake)),
  ).map<ScreeningSuggestion>((r) => {
    const family = intake.family_history.includes(r.cancer_type);
    return {
      rule_id: r.id,
      cancer_type: r.cancer_type,
      method: r.method,
      start_age: r.start_age,
      interval_months: r.interval_months,
      applies_because: r.applies_because,
      note: family ? r.family_note : null,
      elevated_risk: family,
      sources: [GUIDELINE_SOURCES[r.doc_id]],
    };
  });
  return { evaluated: true, suggestions, risk_factors };
}

// ---------------------------------------------------------------- triage
function serviceFor(cancer_type: CancerType): string {
  return SERVICES.find((s) => s.cancer_types.includes(cancer_type))?.code ?? "general_screening";
}

export function triage(
  intake: IntakeProfile,
  redFlag: RedFlagResult,
  suggestions: ScreeningSuggestion[],
  riskFactors: RiskFactor[],
): { next_action: NextAction; booking_hint: BookingHint | null } {
  if (redFlag.detected) {
    return {
      next_action: "urgent_care",
      booking_hint: {
        priority: "urgent",
        service_codes: ["oncology_priority"],
        reason: `Có dấu hiệu cần khám sớm: ${redFlag.flags.map((f) => f.symptom.toLowerCase()).join(", ")}.`,
      },
    };
  }
  if (intake.personal_cancer_history) {
    return {
      next_action: "suggest_booking",
      booking_hint: {
        priority: "routine",
        service_codes: ["oncology_followup"],
        reason: "Người đã từng được chẩn đoán ung thư cần kế hoạch theo dõi của bác sĩ chuyên khoa.",
      },
    };
  }
  const flagged = riskFactors.filter((f) => f.level !== "average").map((f) => f.cancer_type);
  const types = uniq([...suggestions.map((s) => s.cancer_type), ...flagged]);
  if (types.length === 0) return { next_action: "continue_chat", booking_hint: null };
  // Câu trung tính (mirror ai_core/tools/triage.py): dùng cho CTA và làm lý do khám mặc định.
  const reasons: string[] = [];
  if (suggestions.length) {
    reasons.push(
      `Thuộc nhóm có mốc tầm soát theo hướng dẫn: ${suggestions.map((s) => LABEL_VI[s.cancer_type]).join(", ")}`,
    );
  }
  if (flagged.length) {
    reasons.push(
      `yếu tố nguy cơ cần bác sĩ đánh giá: ${riskFactors
        .flatMap((f) => f.reasons)
        .join("; ")
        .toLowerCase()}`,
    );
  }
  return {
    next_action: "suggest_booking",
    booking_hint: {
      priority: "routine",
      service_codes: uniq(types.map(serviceFor)),
      reason: `${reasons.join("; ")}.`,
    },
  };
}

// ---------------------------------------------------------------- Navigator
const GENDER_VI: Record<Gender, string> = { female: "nữ", male: "nam", other: "giới tính khác" };
const MISSING_VI: Record<string, string> = {
  age: "tuổi",
  gender: "giới tính",
  pack_years: "số gói-năm đã hút (số gói/ngày × số năm)",
};

function intervalVi(months: number | null): string {
  if (months === null) return "tần suất do bác sĩ cùng quyết định";
  if (months % 12 === 0) return months === 12 ? "mỗi năm" : `mỗi ${months / 12} năm`;
  return `mỗi ${months} tháng`;
}

// Yêu cầu chẩn đoán / đọc kết quả / điều trị (câu hỏi về chính người dùng, không phải mô tả tiền sử người thân).
const OUT_OF_SCOPE =
  /(chan doan (giup|cho toi|cho minh|xem)|co phai (toi |minh )?(bi )?ung thu|(toi|minh) co bi ung thu (khong|ko|chua)|doc (giup |ho )?ket qua|ket qua (xet nghiem|sieu am|chup)[^.?!]*(the nao|co sao|binh thuong)|dieu tri (the nao|bang gi|o dau)|uong thuoc gi|ke don)/;
const QUESTION = /(\?|\b(la gi|the nao|bao lau|bao nhieu|co can|co nen|khi nao|o dau|tai sao|vi sao|nhu the nao|ai nen|co dau|co sao)\b)/;

export interface NavigatorOutcome {
  reply: NavigatorReply;
  events: TraceEvent[];
  outOfScope: boolean;
}

export function runNavigator(intake: IntakeProfile, message: string | null): NavigatorOutcome {
  const trace_id = newTraceId();
  const folded = message ? fold(message) : "";
  const outOfScope = Boolean(message) && OUT_OF_SCOPE.test(folded);
  const red_flag = redFlagFor(intake.symptom_codes);
  const missing_info = missingInfo(intake);
  const events: TraceEvent[] = [
    { node: "input_guard", ms: 1, out_of_scope: outOfScope },
    { node: "update_intake", ms: 2, missing: missing_info.length },
    { node: "red_flag", ms: 1, detected: red_flag.detected, flag_count: red_flag.flags.length },
  ];

  if (red_flag.detected) {
    const { next_action, booking_hint } = triage(intake, red_flag, [], []);
    const reply = [
      red_flag.message ?? RED_FLAG_MESSAGE,
      ...red_flag.flags.map((f) => `• ${f.symptom}: ${f.advice}`),
      "Bạn có thể tạo tài khoản để đặt lịch khám ưu tiên, hoặc đến cơ sở y tế gần nhất. Nếu triệu chứng nặng lên đột ngột, hãy gọi cấp cứu 115.",
    ].join("\n");
    events.push({ node: "triage", ms: 1, next_action });
    return {
      outOfScope,
      events,
      reply: {
        reply,
        sources: [],
        intake,
        missing_info,
        suggestions: [],
        risk_factors: [],
        red_flag,
        next_action,
        booking_hint,
        insufficient_evidence: false,
        disclaimer: DISCLAIMER,
        trace_id,
        trace_events: [],
      },
    };
  }

  const { evaluated, suggestions, risk_factors } = evaluate(intake);
  events.push({ node: "eligibility", ms: 2, evaluated, suggestion_count: suggestions.length });

  const parts: string[] = [];
  let sources: Source[] = suggestions.flatMap((s) => s.sources);
  if (outOfScope) {
    parts.push(
      "Mình không thể chẩn đoán, đọc kết quả xét nghiệm/hình ảnh hay tư vấn điều trị; việc này cần bác sĩ đánh giá trực tiếp. Bạn có thể đặt lịch để được bác sĩ tư vấn.",
    );
  }
  if (suggestions.length && intake.gender && intake.age !== null) {
    parts.push(
      `Với thông tin bạn cung cấp (${GENDER_VI[intake.gender]}, ${intake.age} tuổi), các hướng dẫn tầm soát hiện có gợi ý:`,
    );
    suggestions.forEach((s) => {
      let line = `• ${LABEL_VI[s.cancer_type]}: ${s.method}, ${intervalVi(s.interval_months)} (${s.applies_because}).`;
      if (s.note) line += ` Lưu ý: ${s.note}`;
      parts.push(line);
    });
  } else if (evaluated && !intake.personal_cancer_history) {
    parts.push(
      "Với độ tuổi và giới tính hiện tại, bộ hướng dẫn của hệ thống chưa có mốc tầm soát định kỳ nào áp dụng cho bạn.",
    );
  }
  if (intake.personal_cancer_history) {
    parts.push(
      "Bạn cho biết đã từng được chẩn đoán ung thư: các mốc tầm soát cho người chưa mắc bệnh không áp dụng; kế hoạch theo dõi cần bác sĩ chuyên khoa ung bướu xây dựng.",
    );
  }
  const covered = new Set(suggestions.map((s) => s.cancer_type));
  risk_factors.forEach((f) => {
    if (f.level !== "average" && !covered.has(f.cancer_type)) {
      parts.push(
        `Bạn có yếu tố cần lưu ý (${f.reasons.join("; ").toLowerCase()}), nên trao đổi với bác sĩ về thời điểm và phương pháp tầm soát ${LABEL_VI[f.cancer_type]} phù hợp.`,
      );
    }
  });
  let retrieved = 0;
  if (message && !outOfScope) {
    const faq = FAQ.find((f) => f.match.test(folded));
    if (faq) {
      const src = GUIDELINE_SOURCES[faq.doc_id];
      parts.push(`Thông tin liên quan từ ${src.title} (${src.section ?? "tổng quan"}): ${faq.answer}`);
      sources.push(src);
      retrieved = 1;
    }
  }
  events.push({ node: "retrieve", ms: 3, mode: "lexical", source_count: retrieved });
  if (missing_info.length) {
    parts.push(
      `Để gợi ý chính xác hơn, bạn cho mình biết thêm ${missing_info.map((m) => MISSING_VI[m] ?? m).join(", ")} nhé?`,
    );
  }
  if (!parts.length) {
    parts.push(
      "Mình là trợ lý tầm soát ung thư. Bạn có thể hỏi về loại ung thư nên tầm soát, thời điểm bắt đầu và tần suất; hoặc làm bảng hỏi nhanh để nhận gợi ý theo tuổi, giới và yếu tố nguy cơ.",
    );
  }
  sources = uniqSources(sources);
  const insufficient_evidence = Boolean(message) && !outOfScope && sources.length === 0 && QUESTION.test(folded);
  if (insufficient_evidence) {
    parts.push(
      "Hiện mình chưa có tài liệu hướng dẫn phù hợp để trả lời câu hỏi này một cách có căn cứ. Bạn nên trao đổi trực tiếp với bác sĩ.",
    );
  }
  events.push({ node: "respond", ms: 4, generator: "template" });

  const { next_action, booking_hint } = triage(intake, red_flag, suggestions, risk_factors);
  events.push({ node: "triage", ms: 1, next_action });

  return {
    outOfScope,
    events,
    reply: {
      reply: parts.join("\n"),
      sources,
      intake,
      missing_info,
      suggestions,
      risk_factors,
      red_flag,
      next_action,
      booking_hint,
      insufficient_evidence,
      disclaimer: DISCLAIMER,
      trace_id,
      trace_events: [],
    },
  };
}

export function assertNavigatorInvariants(r: NavigatorReply): void {
  if (r.red_flag.detected && (r.next_action !== "urgent_care" || r.suggestions.length > 0)) {
    throw new Error("mock invariant: red-flag phải là urgent_care và không có suggestion");
  }
  if ((r.next_action === "suggest_booking" || r.next_action === "urgent_care") && !r.booking_hint) {
    throw new Error("mock invariant: booking route thiếu booking_hint");
  }
  if (r.suggestions.some((s) => s.sources.length === 0)) {
    throw new Error("mock invariant: suggestion thiếu nguồn");
  }
}

// ---------------------------------------------------------------- Clinical Copilot
const FACT_KINDS = new Set([
  "consult.summary",
  "red_flag.detected",
  "appointment.requested",
  "encounter.finalized",
  "reminder.done",
  "profile.updated",
]);

export function recordSource(e: RecordEventOut): Source {
  return { doc_id: `record:${e.id}`, title: "Hồ sơ bệnh nhân", section: e.kind, excerpt: e.summary, url: null };
}

export interface BriefInput {
  fullName: string;
  profile: PatientProfileOut | null;
  consultIntake: IntakeProfile | null;
  events: RecordEventOut[];
  reason: string | null;
}

export function buildBrief(input: BriefInput): ClinicalBrief {
  const t0 = Date.now();
  const intake = mergeIntake(input.profile ? intakeFromProfile(input.profile) : null, input.consultIntake);
  const codes = [...intake.symptom_codes];
  input.events.forEach((e) => {
    if (e.kind === "red_flag.detected" && Array.isArray(e.data.codes)) {
      codes.push(...(e.data.codes as unknown[]).map(String));
    }
  });
  const red = redFlagFor(uniq(codes));
  const key_facts: BriefFact[] = input.events
    .filter((e) => FACT_KINDS.has(e.kind))
    .map((e) => ({ text: e.summary, event_ids: [e.id] }));

  const result = evaluate(intake);
  // Có red-flag: ưu tiên đánh giá triệu chứng → không đưa gợi ý tầm soát định kỳ và không soạn kế hoạch nháp.
  const suggestions = red.detected ? [] : result.suggestions;
  const screened = new Set<string>();
  input.events.forEach((e) => {
    if ((e.kind === "reminder.done" || e.kind === "encounter.finalized") && Array.isArray(e.data.cancer_types)) {
      (e.data.cancer_types as unknown[]).forEach((c) => screened.add(String(c)));
    }
  });

  const data_gaps: string[] = [];
  const questions: string[] = [];
  if (intake.age === null) data_gaps.push("Thiếu tuổi.");
  if (intake.gender === null) data_gaps.push("Thiếu giới tính.");
  if (red.detected) {
    data_gaps.push("Có dấu hiệu cảnh báo: ưu tiên đánh giá chẩn đoán; chưa soạn kế hoạch tầm soát định kỳ.");
    questions.push(`Thời điểm xuất hiện và diễn tiến của: ${red.flags.map((f) => f.symptom.toLowerCase()).join(", ")}?`);
  }
  suggestions.forEach((s) => {
    if (!screened.has(s.cancer_type)) {
      data_gaps.push(`Chưa ghi nhận lần tầm soát ${LABEL_VI[s.cancer_type]} gần nhất (ngày, phương pháp).`);
      questions.push(`Lần tầm soát ${LABEL_VI[s.cancer_type]} gần nhất là khi nào, bằng phương pháp gì?`);
    }
  });
  if (intake.smoking && intake.pack_years === null) {
    data_gaps.push("Chưa có số gói-năm.");
    questions.push("Ước tính số gói-năm (số gói/ngày × số năm hút)?");
  }
  if (suggestions.some((s) => s.cancer_type === "lung")) {
    questions.push("Hiện còn hút thuốc không? Nếu đã bỏ, cách đây bao nhiêu năm (tiêu chí ≤ 15 năm)?");
  }
  intake.family_history.forEach((t) => {
    if (t !== "other") questions.push(`Người thân nào mắc ${LABEL_VI[t]}, phát hiện ở tuổi nào?`);
  });
  if (intake.hepatitis_b_or_c || intake.cirrhosis) {
    questions.push("Tình trạng viêm gan/xơ gan hiện tại và lần đánh giá xơ hoá gan gần nhất?");
  }

  const who = [
    input.fullName,
    intake.gender ? GENDER_VI[intake.gender] : null,
    intake.age !== null ? `${intake.age} tuổi` : null,
  ]
    .filter(Boolean)
    .join(", ");
  const summaryParts = [who ? `Bệnh nhân ${who}.` : "Bệnh nhân chưa có đủ thông tin nhân khẩu."];
  if (input.reason) summaryParts.push(`Lý do khám: ${input.reason}`);
  if (red.detected) {
    summaryParts.push(`Có dấu hiệu cảnh báo: ${red.flags.map((f) => f.symptom.toLowerCase()).join(", ")}.`);
  }
  if (result.risk_factors.length) {
    summaryParts.push(
      `Yếu tố nguy cơ ghi nhận: ${result.risk_factors
        .flatMap((f) => f.reasons)
        .join("; ")
        .toLowerCase()}.`,
    );
  }
  if (suggestions.length) {
    summaryParts.push(
      `Guideline gợi ý: ${suggestions.map((s) => `${LABEL_VI[s.cancer_type]} (${s.method})`).join("; ")}.`,
    );
  }

  let draft_plan: ScreeningPlan | null = null;
  if (!red.detected) {
    const items: PlanItem[] = suggestions
      .filter((s): s is ScreeningSuggestion & { interval_months: number } => s.interval_months !== null)
      .map((s) => ({
        cancer_type: s.cancer_type,
        method: s.method,
        start_age: s.start_age,
        interval_months: s.interval_months,
        next_due: null,
        rationale: [`${s.applies_because}.`, s.note].filter(Boolean).join(" "),
        sources: s.sources,
        priority: s.elevated_risk ? 1 : 2,
      }));
    if (items.length) {
      draft_plan = {
        items,
        general_advice: "Bác sĩ xác nhận ngày hẹn dựa trên lịch sử tầm soát trước khi phê duyệt.",
        generated_at: new Date().toISOString(),
        model: MOCK_MODEL,
      };
    }
  }

  const brief: ClinicalBrief = {
    summary: summaryParts.join(" "),
    key_facts,
    red_flags: red.flags,
    risk_factors: result.risk_factors,
    guideline_suggestions: suggestions,
    questions_to_clarify: uniq(questions).slice(0, 8),
    data_gaps,
    draft_plan,
    disclaimer: COPILOT_DISCLAIMER,
    generated_at: new Date().toISOString(),
    model: MOCK_MODEL,
    trace_id: newTraceId(),
    trace_events: [
      { node: "load_record", ms: 3, event_count: input.events.length, red_flag: red.detected },
      { node: "eligibility", ms: 2, suggestion_count: suggestions.length, gap_count: data_gaps.length },
      { node: "retrieve", ms: 5, mode: "lexical", source_count: uniqSources(suggestions.flatMap((s) => s.sources)).length },
      { node: "draft_brief", ms: 1, generator: "template" },
      { node: "draft_plan", ms: 1, has_plan: draft_plan !== null, item_count: draft_plan?.items.length ?? 0 },
      { node: "total", ms: Math.max(1, Date.now() - t0) + 12 },
    ],
  };
  assertBriefInvariants(brief);
  return brief;
}

export function assertBriefInvariants(b: ClinicalBrief): void {
  if (b.red_flags.length && (b.draft_plan || b.guideline_suggestions.length)) {
    throw new Error("mock invariant: brief có red-flag không được có gợi ý/kế hoạch nháp");
  }
  if (b.guideline_suggestions.some((s) => s.sources.length === 0) || b.draft_plan?.items.some((i) => i.sources.length === 0)) {
    throw new Error("mock invariant: thiếu nguồn");
  }
}

const DIAGNOSIS_REQUEST = /(chan doan|co bi ung thu|bi ung thu khong|ac tinh|lanh tinh|doc (giup )?ket qua|dien giai ket qua|ket qua (xet nghiem|sieu am|chup|sinh thiet))/;

export function copilotAnswer(question: string, brief: ClinicalBrief | null, events: RecordEventOut[]): QuestionAnswer {
  const q = fold(question);
  const trace_id = newTraceId();
  const base = { disclaimer: COPILOT_DISCLAIMER, trace_id };
  if (DIAGNOSIS_REQUEST.test(q)) {
    return {
      ...base,
      answer:
        "Copilot không đưa ra chẩn đoán và không diễn giải kết quả cận lâm sàng. Tôi có thể tóm tắt dữ kiện trong hồ sơ hoặc đối chiếu guideline tầm soát có trích dẫn để bác sĩ tham khảo.",
      sources: [],
      insufficient_evidence: true,
      trace_events: [{ node: "input_guard", ms: 1, blocked: true, reason: "diagnosis_request" }],
    };
  }
  const recordHits: RecordEventOut[] = [];
  const lines: string[] = [];
  const guideline: Source[] = [];

  if (/(tien su|gia dinh|nguoi than|di truyen)/.test(q)) {
    const hits = events.filter((e) => /(nguoi than|gia dinh|me |bo |chi |tien su)/.test(fold(e.summary)));
    recordHits.push(...hits);
    lines.push(
      hits.length
        ? `Dữ kiện tiền sử trong hồ sơ: ${hits.map((e) => e.summary).join(" ")}`
        : "Hồ sơ chưa ghi nhận chi tiết tiền sử gia đình; nên hỏi trực tiếp bệnh nhân.",
    );
  }
  if (/(trieu chung|canh bao|red.?flag|kham som|uu tien)/.test(q)) {
    const hits = events.filter((e) => e.kind === "red_flag.detected");
    recordHits.push(...hits);
    lines.push(
      hits.length
        ? `Hồ sơ ghi nhận dấu hiệu cần khám sớm: ${hits.map((e) => e.summary).join(" ")} Cần đánh giá lâm sàng trực tiếp trước khi cân nhắc tầm soát định kỳ.`
        : "Hồ sơ không ghi nhận dấu hiệu cảnh báo trong các lượt tư vấn.",
    );
  }
  if (/(ke hoach|lich tam soat|plan|nhac lich|next due|ngay hen)/.test(q) && brief?.draft_plan) {
    lines.push(
      `Kế hoạch nháp gồm: ${brief.draft_plan.items
        .map((i) => `${LABEL_VI[i.cancer_type]} (${i.method}, ${intervalVi(i.interval_months)})`)
        .join("; ")}. Ngày hẹn (next_due) do bác sĩ điền khi duyệt.`,
    );
    guideline.push(...brief.draft_plan.items.flatMap((i) => i.sources));
  }
  const faq = FAQ.find((f) => f.match.test(q));
  if (faq) {
    const src = GUIDELINE_SOURCES[faq.doc_id];
    lines.push(`Theo ${src.title}: ${src.excerpt}`);
    guideline.push(src);
  }
  if (!lines.length) {
    if (!brief) {
      return {
        ...base,
        answer: "Chưa có tóm tắt hồ sơ cho lượt khám này. Hãy tạo lại brief rồi hỏi tiếp.",
        sources: [],
        insufficient_evidence: true,
        trace_events: [{ node: "retrieve", ms: 2, record_hits: 0, guideline_hits: 0 }],
      };
    }
    const facts = brief.key_facts.slice(0, 3);
    facts.forEach((f) => recordHits.push(...events.filter((e) => f.event_ids.includes(e.id))));
    lines.push(`Tóm tắt: ${brief.summary}`);
    if (brief.questions_to_clarify.length) lines.push(`Nên làm rõ: ${brief.questions_to_clarify.slice(0, 2).join(" ")}`);
  }
  const sources = uniqSources([...uniqSourcesFromEvents(recordHits), ...guideline]);
  return {
    ...base,
    answer: lines.join("\n"),
    sources,
    insufficient_evidence: sources.length === 0,
    trace_events: [
      { node: "input_guard", ms: 1, blocked: false },
      { node: "retrieve", ms: 4, record_hits: recordHits.length, guideline_hits: guideline.length },
      { node: "answer", ms: 2, generator: "template", cited: sources.length },
    ],
  };
}

function uniqSourcesFromEvents(events: RecordEventOut[]): Source[] {
  const byId = new Map<string, RecordEventOut>();
  events.forEach((e) => byId.set(e.id, e));
  return Array.from(byId.values()).map(recordSource);
}

export function patientPlanAnswer(question: string, plan: ScreeningPlan | null): QuestionAnswer {
  const q = fold(question);
  const trace_id = newTraceId();
  const base = { disclaimer: DISCLAIMER, trace_id, trace_events: [] as TraceEvent[] };
  if (DIAGNOSIS_REQUEST.test(q) || /(toi co bi|co nguy hiem khong|bi benh gi)/.test(q)) {
    return {
      ...base,
      answer:
        "Trợ lý không thể chẩn đoán hay diễn giải kết quả xét nghiệm. Câu hỏi này bạn nên trao đổi trực tiếp với bác sĩ đã khám cho bạn.",
      sources: [],
      insufficient_evidence: true,
    };
  }
  if (!plan || plan.items.length === 0) {
    return {
      ...base,
      answer:
        "Lần khám này bác sĩ không lập kế hoạch tầm soát định kỳ, nên trợ lý chưa có căn cứ để giải thích thêm. Hãy làm theo lời dặn của bác sĩ và liên hệ bệnh viện nếu cần.",
      sources: [],
      insufficient_evidence: true,
    };
  }
  const matched = plan.items.filter((i) => q.includes(fold(LABEL_VI[i.cancer_type]).replace("ung thu ", "")) || q.includes(fold(i.method).split(" (")[0]));
  const items = matched.length ? matched : plan.items;
  const lines = items.map(
    (i) =>
      `• ${LABEL_VI[i.cancer_type]}: ${i.method}, ${intervalVi(i.interval_months)}${
        i.next_due ? `, lần tới khoảng ${i.next_due}` : ""
      }. ${i.rationale}`,
  );
  return {
    ...base,
    answer: ["Theo kế hoạch bác sĩ đã duyệt cho bạn:", ...lines, "Nếu có thay đổi sức khoẻ hoặc triệu chứng mới, hãy liên hệ bác sĩ thay vì chờ đến lịch hẹn."].join("\n"),
    sources: uniqSources(items.flatMap((i) => i.sources)),
    insufficient_evidence: false,
  };
}
