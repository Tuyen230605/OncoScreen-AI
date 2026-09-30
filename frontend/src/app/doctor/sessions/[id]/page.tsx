"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import type { ScreeningPlan, SessionOut } from "@/types/api";
import { PlanTable } from "@/components/PlanTable";
import { RedFlagAlert } from "@/components/RedFlagAlert";
import { Disclaimer } from "@/components/Disclaimer";
import { SessionStatusBadge } from "@/components/SessionStatusBadge";

/**
 * Màn duyệt HITL cho bác sĩ (Tuần 3).
 * Hiển thị: answers của bệnh nhân, risk assessment AI, draft plan editable, approve/reject với note.
 */
export default function DoctorSessionPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [session, setSession] = useState<SessionOut | null>(null);
  const [plan, setPlan] = useState<ScreeningPlan | null>(null);
  const [note, setNote] = useState("");
  const [acting, setActing] = useState<"approve" | "reject" | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getSession(params.id)
      .then((x) => {
        setSession(x);
        setPlan(x.draft_plan ?? x.final_plan);
      })
      .catch(console.error);
  }, [params.id]);

  async function act(action: "approve" | "reject") {
    if (action === "reject" && !note.trim()) {
      setError("Từ chối bắt buộc phải ghi lý do.");
      return;
    }
    setError("");
    setActing(action);
    try {
      await api.review(params.id, {
        action,
        final_plan: action === "approve" && plan ? plan : undefined,
        note: note.trim() || undefined,
      });
      router.push("/doctor");
    } catch {
      setError("Thao tác thất bại. Vui lòng thử lại.");
      setActing(null);
    }
  }

  if (!session) {
    return (
      <div className="flex min-h-[300px] items-center justify-center">
        <span className="spinner h-6 w-6 text-blue-500" aria-label="Đang tải…" />
      </div>
    );
  }

  const riskLevelColor: Record<string, string> = {
    average: "bg-green-50 text-green-700 border-green-200",
    elevated: "bg-yellow-50 text-yellow-700 border-yellow-200",
    high: "bg-red-50 text-red-700 border-red-200",
  };

  const riskLevelLabel: Record<string, string> = {
    average: "Nguy cơ trung bình",
    elevated: "Nguy cơ tăng",
    high: "Nguy cơ cao",
  };

  const boolLabel = (v: unknown) => {
    if (v === true || v === "true") return "Có";
    if (v === false || v === "false") return "Không";
    return String(v ?? "—");
  };

  return (
    <div className="fade-in space-y-6">
      {/* Back + header */}
      <div>
        <Link href="/doctor" className="text-sm text-blue-600 hover:underline">
          ← Quay lại hàng chờ
        </Link>
        <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="page-title">Phiên đánh giá — {session.patient_name}</h1>
            <p className="page-subtitle">
              {new Date(session.created_at).toLocaleDateString("vi-VN", {
                weekday: "long",
                day: "numeric",
                month: "long",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {session.has_red_flag && (
              <span className="rounded-full bg-red-600 px-3 py-1 text-xs font-bold text-white">KHẨN</span>
            )}
            <SessionStatusBadge status={session.status} />
          </div>
        </div>
      </div>

      {/* Red Flag Alert */}
      {session.red_flag?.detected && <RedFlagAlert result={session.red_flag} />}

      {/* Patient Answers */}
      {session.answers && session.answers.length > 0 && (
        <section className="card-padded space-y-3">
          <h2 className="font-semibold text-slate-800 flex items-center gap-2">
            <span>📝</span> Câu trả lời của bệnh nhân
          </h2>
          <dl className="divide-y divide-slate-100">
            {session.answers.map((a) => (
              <div key={a.question_id} className="flex gap-4 py-2 text-sm">
                <dt className="w-48 shrink-0 text-slate-500 font-medium">{a.question_id}</dt>
                <dd className="text-slate-800">
                  {Array.isArray(a.value) ? (a.value as string[]).join(", ") : boolLabel(a.value)}
                </dd>
              </div>
            ))}
          </dl>
        </section>
      )}

      {/* Risk Assessment */}
      {session.risk_assessment && (
        <section className="card-padded space-y-3">
          <h2 className="font-semibold text-slate-800 flex items-center gap-2">
            <span>🔬</span> Đánh giá nguy cơ (AI)
          </h2>
          <p className="text-sm text-slate-700">{session.risk_assessment.overall_summary}</p>
          <div className="grid gap-3 sm:grid-cols-2">
            {session.risk_assessment.factors.map((f) => (
              <div
                key={f.cancer_type}
                className={`rounded-lg border p-3 text-sm ${riskLevelColor[f.level] ?? "bg-slate-50"}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold uppercase">{f.cancer_type}</span>
                  <span className="text-xs font-medium">{riskLevelLabel[f.level] ?? f.level}</span>
                </div>
                <ul className="list-disc pl-4 space-y-0.5">
                  {f.reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Draft Plan — editable only for pending_review */}
      {plan && (
        <section className="card-padded space-y-3">
          <h2 className="font-semibold text-slate-800 flex items-center gap-2">
            <span>📋</span>
            {session.status === "pending_review"
              ? "Bản nháp kế hoạch tầm soát (AI) — bác sĩ có thể chỉnh sửa"
              : "Kế hoạch tầm soát"}
          </h2>
          <PlanTable
            plan={plan}
            editable={session.status === "pending_review"}
            onChange={setPlan}
          />
        </section>
      )}

      {/* Already reviewed info */}
      {(session.status === "approved" || session.status === "rejected") && session.reviewed_by && (
        <section className="card-padded text-sm text-slate-600 space-y-1">
          <p className="flex items-center gap-1.5">
            {session.status === "approved" ? "✅" : "❌"}
            <span>
              {session.status === "approved" ? "Đã phê duyệt" : "Đã từ chối"} bởi{" "}
              <strong>{session.reviewed_by.full_name}</strong>
              {session.reviewed_at && (
                <>
                  {" · "}
                  {new Date(session.reviewed_at).toLocaleString("vi-VN", {
                    hour: "2-digit",
                    minute: "2-digit",
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                  })}
                </>
              )}
            </span>
          </p>
          {session.doctor_note && (
            <p className="rounded bg-slate-50 border border-slate-200 p-2 text-slate-700">
              <span className="font-medium">Ghi chú:</span> {session.doctor_note}
            </p>
          )}
        </section>
      )}

      {/* HITL Actions — only for pending_review */}
      {session.status === "pending_review" && (
        <section className="card-padded space-y-3">
          <h2 className="font-semibold text-slate-800">Quyết định</h2>
          <div>
            <label htmlFor="doctor-note" className="block text-sm font-medium text-slate-700 mb-1">
              Ghi chú cho bệnh nhân{" "}
              <span className="text-slate-400 font-normal">(bắt buộc nếu từ chối)</span>
            </label>
            <textarea
              id="doctor-note"
              rows={3}
              className="input w-full resize-y"
              placeholder="Nhập lý do từ chối hoặc ghi chú hướng dẫn thêm cho bệnh nhân…"
              value={note}
              onChange={(e) => {
                setNote(e.target.value);
                setError("");
              }}
            />
          </div>

          {error && (
            <p className="rounded bg-red-50 border border-red-200 p-2 text-sm text-red-700">{error}</p>
          )}

          <div className="flex flex-wrap gap-3">
            <button
              id="btn-approve"
              onClick={() => act("approve")}
              disabled={acting !== null}
              className="btn-primary flex items-center gap-2"
            >
              {acting === "approve" ? <span className="spinner h-4 w-4" /> : "✅"}
              {acting === "approve" ? "Đang phê duyệt…" : "Phê duyệt kế hoạch"}
            </button>
            <button
              id="btn-reject"
              onClick={() => act("reject")}
              disabled={acting !== null}
              className="btn-secondary flex items-center gap-2 border-red-200 text-red-700 hover:bg-red-50"
            >
              {acting === "reject" ? <span className="spinner h-4 w-4" /> : "❌"}
              {acting === "reject" ? "Đang từ chối…" : "Từ chối"}
            </button>
          </div>
          <p className="text-xs text-slate-400">
            Phê duyệt sẽ gửi kế hoạch tầm soát đến bệnh nhân và tạo lịch nhắc tự động.
          </p>
        </section>
      )}

      <Disclaimer text={session.disclaimer} />
    </div>
  );
}
