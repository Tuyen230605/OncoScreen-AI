"use client";
import { Suspense, useEffect, useReducer } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Answer, Question, Questionnaire, SessionOut } from "@/types/api";
import { Disclaimer } from "@/components/Disclaimer";

// ─── State management ──────────────────────────────────────────────────────────

interface SurveyState {
  session: SessionOut | null;
  questionnaire: Questionnaire | null;
  answers: Record<string, unknown>;
  /** Bước wizard: index trong visible questions */
  step: number;
  /** Đang submit */
  submitting: boolean;
  /** Lỗi */
  error: string;
}

type Action =
  | { type: "SET_SESSION"; payload: SessionOut }
  | { type: "SET_ANSWER"; id: string; value: unknown }
  | { type: "TOGGLE_MULTI"; id: string; value: string; checked: boolean }
  | { type: "NEXT" }
  | { type: "PREV" }
  | { type: "SET_SUBMITTING"; v: boolean }
  | { type: "SET_ERROR"; msg: string };

function reducer(state: SurveyState, action: Action): SurveyState {
  switch (action.type) {
    case "SET_SESSION":
      return { ...state, session: action.payload, questionnaire: action.payload.questionnaire ?? null };
    case "SET_ANSWER":
      return { ...state, answers: { ...state.answers, [action.id]: action.value }, error: "" };
    case "TOGGLE_MULTI": {
      const cur = new Set((state.answers[action.id] as string[] | undefined) ?? []);
      action.checked ? cur.add(action.value) : cur.delete(action.value);
      return { ...state, answers: { ...state.answers, [action.id]: [...cur] } };
    }
    case "NEXT":
      return { ...state, step: state.step + 1, error: "" };
    case "PREV":
      return { ...state, step: Math.max(0, state.step - 1), error: "" };
    case "SET_SUBMITTING":
      return { ...state, submitting: action.v };
    case "SET_ERROR":
      return { ...state, error: action.msg };
    default:
      return state;
  }
}

const initState: SurveyState = { session: null, questionnaire: null, answers: {}, step: 0, submitting: false, error: "" };

// ─── Helpers ───────────────────────────────────────────────────────────────────

/** Kiểm tra question phụ thuộc (depends_on = "question_id=value") */
function isVisible(q: Question, answers: Record<string, unknown>): boolean {
  if (!q.depends_on) return true;
  const [k, v] = q.depends_on.split("=");
  return String(answers[k] ?? "").toLowerCase() === v.toLowerCase();
}

const CANCER_TYPE_LABELS: Record<string, string> = {
  breast: "Ung thư vú",
  lung: "Ung thư phổi",
  colorectal: "Ung thư đại trực tràng",
  cervical: "Ung thư cổ tử cung",
  liver: "Ung thư gan",
  prostate: "Ung thư tuyến tiền liệt",
  other: "Khác",
};

// ─── QuestionCard ───────────────────────────────────────────────────────────────

function QuestionCard({
  q,
  value,
  onChange,
  onMultiToggle,
}: {
  q: Question;
  value: unknown;
  onChange: (id: string, v: unknown) => void;
  onMultiToggle: (id: string, v: string, checked: boolean) => void;
}) {
  return (
    <div className="card-padded fade-in space-y-3">
      <label htmlFor={`q-${q.id}`} className="block text-base font-medium text-slate-900">
        {q.text}
        {q.required && <span className="ml-1 text-red-500" aria-hidden>*</span>}
      </label>

      {/* Boolean */}
      {q.type === "boolean" && (
        <div className="flex gap-3">
          {(["true", "false"] as const).map((v) => (
            <label
              key={v}
              className={`flex flex-1 cursor-pointer items-center justify-center gap-2 rounded-lg border-2 p-3 text-sm font-medium transition-all ${
                String(value) === v
                  ? "border-blue-500 bg-blue-50 text-blue-700"
                  : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
              }`}
            >
              <input
                type="radio"
                name={q.id}
                value={v}
                checked={String(value) === v}
                onChange={() => onChange(q.id, v === "true")}
                className="sr-only"
              />
              {v === "true" ? "✓ Có" : "✗ Không"}
            </label>
          ))}
        </div>
      )}

      {/* Number */}
      {q.type === "number" && (
        <input
          id={`q-${q.id}`}
          type="number"
          min={0}
          value={(value as number | undefined) ?? ""}
          onChange={(e) => onChange(q.id, e.target.value === "" ? undefined : Number(e.target.value))}
          className="input max-w-xs"
          placeholder="Nhập số…"
        />
      )}

      {/* Text */}
      {q.type === "text" && (
        <input
          id={`q-${q.id}`}
          type="text"
          value={(value as string | undefined) ?? ""}
          onChange={(e) => onChange(q.id, e.target.value)}
          className="input"
          placeholder="Nhập câu trả lời…"
        />
      )}

      {/* Single choice */}
      {q.type === "single_choice" && (
        <div className="flex flex-col gap-2">
          {q.options?.map((o) => (
            <label
              key={o}
              className={`flex cursor-pointer items-center gap-3 rounded-lg border-2 p-3 text-sm transition-all ${
                value === o
                  ? "border-blue-500 bg-blue-50 text-blue-700"
                  : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
              }`}
            >
              <input
                type="radio"
                name={q.id}
                value={o}
                checked={value === o}
                onChange={() => onChange(q.id, o)}
                className="accent-blue-600"
              />
              {CANCER_TYPE_LABELS[o] ?? o}
            </label>
          ))}
        </div>
      )}

      {/* Multi choice */}
      {q.type === "multi_choice" && (
        <div className="flex flex-col gap-2">
          {q.options?.map((o) => {
            const checked = ((value as string[] | undefined) ?? []).includes(o);
            return (
              <label
                key={o}
                className={`flex cursor-pointer items-center gap-3 rounded-lg border-2 p-3 text-sm transition-all ${
                  checked
                    ? "border-blue-500 bg-blue-50 text-blue-700"
                    : "border-slate-200 bg-white text-slate-700 hover:border-slate-300"
                }`}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(e) => onMultiToggle(q.id, o, e.target.checked)}
                  className="accent-blue-600"
                />
                {CANCER_TYPE_LABELS[o] ?? o}
              </label>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Progress bar ───────────────────────────────────────────────────────────────

function ProgressBar({ current, total }: { current: number; total: number }) {
  const pct = total > 0 ? Math.round(((current + 1) / total) * 100) : 0;
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-slate-500">
        <span>Câu {current + 1} / {total}</span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-blue-500 transition-all duration-300"
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
}

// ─── Main Survey component ───────────────────────────────────────────────────────

function Survey() {
  const params = useSearchParams();
  const router = useRouter();
  const sessionId = params.get("session");
  const [state, dispatch] = useReducer(reducer, initState);

  useEffect(() => {
    if (sessionId) {
      api.getSession(sessionId).then((s) => dispatch({ type: "SET_SESSION", payload: s })).catch(console.error);
    } else {
      api.createSession().then((s) => {
        router.replace(`/patient/survey?session=${s.id}`);
        dispatch({ type: "SET_SESSION", payload: s });
      }).catch(console.error);
    }
  }, [sessionId, router]);

  const { session, questionnaire, answers, step, submitting, error } = state;

  if (!session || !questionnaire) {
    return (
      <div className="flex min-h-[300px] items-center justify-center">
        <span className="spinner h-6 w-6 text-blue-500" aria-label="Đang tải bộ câu hỏi…" />
      </div>
    );
  }

  // Danh sách câu hỏi hiển thị tại bước hiện tại (tính theo logic depends_on)
  const visibleQuestions = questionnaire.questions.filter((q) => isVisible(q, answers));
  const current = visibleQuestions[step];
  const isLast = step === visibleQuestions.length - 1;
  const currentValue = current ? answers[current.id] : undefined;

  /** Validate câu hiện tại trước khi qua bước tiếp */
  function validateCurrent(): boolean {
    if (!current) return true;
    if (!current.required) return true;
    if (current.type === "boolean" && currentValue === undefined) {
      dispatch({ type: "SET_ERROR", msg: "Vui lòng chọn Có hoặc Không." });
      return false;
    }
    if (current.type === "single_choice" && !currentValue) {
      dispatch({ type: "SET_ERROR", msg: "Vui lòng chọn một đáp án." });
      return false;
    }
    if (current.type === "multi_choice" && ((currentValue as string[] | undefined) ?? []).length === 0) {
      dispatch({ type: "SET_ERROR", msg: "Vui lòng chọn ít nhất một đáp án." });
      return false;
    }
    if (current.type === "number" && (currentValue === undefined || currentValue === "")) {
      dispatch({ type: "SET_ERROR", msg: "Vui lòng nhập số." });
      return false;
    }
    return true;
  }

  function handleNext() {
    if (!validateCurrent()) return;
    if (isLast) {
      handleSubmit();
    } else {
      dispatch({ type: "NEXT" });
    }
  }

  async function handleSubmit() {
    if (!validateCurrent()) return;
    const sid = sessionId ?? session?.id;
    if (!sid) return;
    const payload: Answer[] = Object.entries(answers).map(([question_id, value]) => ({ question_id, value }));
    try {
      dispatch({ type: "SET_SUBMITTING", v: true });
      const res = await api.submitAnswers(sid, { answers: payload });
      router.push(`/patient/results/${res.id}`);
    } catch {
      dispatch({ type: "SET_ERROR", msg: "Gửi câu trả lời thất bại. Vui lòng thử lại." });
      dispatch({ type: "SET_SUBMITTING", v: false });
    }
  }

  return (
    <div className="fade-in mx-auto max-w-2xl space-y-6">
      {/* Header */}
      <header>
        <h1 className="page-title">Khảo sát đánh giá nguy cơ ung thư</h1>
        <p className="page-subtitle mt-1">Trả lời thành thật để hệ thống đề xuất kế hoạch tầm soát phù hợp.</p>
      </header>

      {/* Progress */}
      <ProgressBar current={step} total={visibleQuestions.length} />

      {/* Question */}
      {current && (
        <QuestionCard
          q={current}
          value={currentValue}
          onChange={(id, v) => dispatch({ type: "SET_ANSWER", id, value: v })}
          onMultiToggle={(id, v, checked) => dispatch({ type: "TOGGLE_MULTI", id, value: v, checked })}
        />
      )}

      {/* Error */}
      {error && (
        <p role="alert" className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          type="button"
          onClick={() => dispatch({ type: "PREV" })}
          disabled={step === 0}
          className="btn-secondary"
        >
          ← Câu trước
        </button>
        <button
          type="button"
          onClick={handleNext}
          disabled={submitting}
          className="btn-primary"
        >
          {submitting ? <span className="spinner h-4 w-4" /> : null}
          {submitting ? "Đang gửi…" : isLast ? "Gửi câu trả lời ✓" : "Câu tiếp →"}
        </button>
      </div>

      {/* Disclaimer */}
      {session.disclaimer && <Disclaimer text={session.disclaimer} />}
    </div>
  );
}

export default function SurveyPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[300px] items-center justify-center">
          <span className="spinner h-6 w-6 text-blue-500" />
        </div>
      }
    >
      <Survey />
    </Suspense>
  );
}
