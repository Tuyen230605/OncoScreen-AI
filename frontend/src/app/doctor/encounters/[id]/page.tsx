"use client";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { errorMessage, isStatus } from "@/lib/errors";
import { formatDate, formatDateTime } from "@/lib/format";
import type {
  EncounterOut,
  FinalizeEncounterIn,
  PatientRecordOut,
  PlanItem,
  ScreeningPlan,
  ScreeningSuggestion,
} from "@/types/api";
import { BriefPanel } from "@/components/doctor/BriefPanel";
import { CopilotChat } from "@/components/doctor/CopilotChat";
import { TraceEvents } from "@/components/doctor/TraceEvents";
import { Disclaimer } from "@/components/Disclaimer";
import { isValidInterval, PlanTable } from "@/components/PlanTable";
import { ReminderList } from "@/components/RecordSections";
import { RecordTimeline, timelineAnchor } from "@/components/RecordTimeline";
import { EncounterStatusBadge, PriorityBadge } from "@/components/StatusBadge";
import { EmptyState, InlineError, MetaDivider, SkeletonList } from "@/components/ui";
import {
  Activity,
  ArrowLeft,
  CheckCircle2,
  ChevronDown,
  ClipboardCheck,
  History,
  NotebookPen,
  RefreshCw,
  Sparkles,
  UserCircle,
} from "@/components/icons";

/** Giới hạn độ dài theo `FinalizeEncounterIn` của backend. */
const MAX_CONCLUSION = 4000;
const MAX_NOTES = 8000;

const clonePlan = (p: ScreeningPlan | null): ScreeningPlan | null => (p ? (JSON.parse(JSON.stringify(p)) as ScreeningPlan) : null);
const planKey = (p: ScreeningPlan | null) =>
  JSON.stringify(
    p
      ? {
          advice: p.general_advice,
          items: p.items.map((i) => [i.cancer_type, i.method, i.start_age, i.interval_months, i.next_due, i.rationale, i.priority]),
        }
      : null,
  );
const sameItem = (a: { cancer_type: string; method: string }, b: { cancer_type: string; method: string }) =>
  a.cancer_type === b.cancer_type && a.method === b.method;

function suggestionToItem(s: ScreeningSuggestion): PlanItem {
  return {
    cancer_type: s.cancer_type,
    method: s.method,
    start_age: s.start_age,
    interval_months: s.interval_months ?? 0, // null: guideline không quy định → bác sĩ phải đặt chu kỳ
    next_due: null,
    rationale: [`${s.applies_because}.`, s.note].filter(Boolean).join(" "),
    sources: s.sources,
    priority: s.elevated_risk ? 1 : 2,
  };
}

/** Phiên khám: Copilot brief + hồ sơ + chat Copilot + sửa kế hoạch + kết luận & hoàn tất (HITL). */
export default function EncounterPage({ params }: { params: { id: string } }) {
  const [enc, setEnc] = useState<EncounterOut | null>(null);
  const [record, setRecord] = useState<PatientRecordOut | null>(null);
  const [error, setError] = useState("");
  const [notFound, setNotFound] = useState(false);
  const [recordError, setRecordError] = useState("");

  const [plan, setPlan] = useState<ScreeningPlan | null>(null);
  const [includePlan, setIncludePlan] = useState(true);
  const [conclusion, setConclusion] = useState("");
  const [notes, setNotes] = useState("");
  const [highlight, setHighlight] = useState<string[]>([]);
  const [regenerating, setRegenerating] = useState(false);
  const [confirmRegenerate, setConfirmRegenerate] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [finalizing, setFinalizing] = useState(false);
  const [formError, setFormError] = useState("");
  const [notice, setNotice] = useState("");
  const [traceOpen, setTraceOpen] = useState(false);

  const applyEncounter = useCallback((e: EncounterOut, resetPlan: boolean) => {
    setEnc(e);
    if (resetPlan) {
      setPlan(clonePlan(e.draft_plan));
      setIncludePlan(Boolean(e.draft_plan));
    }
  }, []);

  const loadRecord = useCallback((patientId: string) => {
    setRecordError("");
    api
      .getPatientRecord(patientId)
      .then(setRecord)
      .catch((err) => setRecordError(errorMessage(err, "Chưa tải được hồ sơ bệnh nhân.")));
  }, []);

  const load = useCallback(() => {
    setError("");
    api
      .getDoctorEncounter(params.id)
      .then((e) => {
        applyEncounter(e, true);
        loadRecord(e.patient_id);
      })
      .catch((err) => {
        if (isStatus(err, 404)) setNotFound(true);
        else setError(errorMessage(err, "Chưa tải được lượt khám."));
      });
  }, [params.id, applyEncounter, loadRecord]);
  useEffect(load, [load]);

  // Làm nổi bật mốc hồ sơ được dẫn chứng
  useEffect(() => {
    if (!highlight.length) return;
    document.getElementById(timelineAnchor(highlight[0]))?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [highlight]);

  const appointment = useMemo(
    () => record?.appointments.find((a) => a.id === enc?.appointment_id) ?? null,
    [record, enc?.appointment_id],
  );
  const finalized = enc?.status === "finalized";
  const dirty = planKey(plan) !== planKey(enc?.draft_plan ?? null);

  /** Tạo lại tóm tắt thay luôn kế hoạch nháp: nếu bác sĩ đã sửa kế hoạch thì hỏi xác nhận trước. */
  function requestRegenerate() {
    setFormError("");
    if (dirty) setConfirmRegenerate(true);
    else void regenerate();
  }

  async function regenerate() {
    if (!enc) return;
    setConfirmRegenerate(false);
    setRegenerating(true);
    setNotice("");
    setFormError("");
    try {
      const updated = await api.regenerateBrief(enc.id);
      applyEncounter(updated, true);
      loadRecord(updated.patient_id);
      setNotice("Đã tạo lại tóm tắt từ hồ sơ mới nhất. Kế hoạch nháp được cập nhật theo tóm tắt mới.");
    } catch (err) {
      setFormError(errorMessage(err, "Chưa tạo lại được tóm tắt."));
    } finally {
      setRegenerating(false);
    }
  }

  function addSuggestion(s: ScreeningSuggestion) {
    const item = suggestionToItem(s);
    setIncludePlan(true);
    setPlan((prev) => {
      if (prev?.items.some((i) => sameItem(i, item))) return prev;
      return prev
        ? { ...prev, items: [...prev.items, item] }
        : {
            items: [item],
            general_advice: "",
            generated_at: new Date().toISOString(),
            model: "doctor",
          };
    });
  }

  function validate(): string | null {
    if (!conclusion.trim()) return "Vui lòng nhập kết luận / lời dặn gửi bệnh nhân.";
    if (conclusion.trim().length > MAX_CONCLUSION) return `Kết luận tối đa ${MAX_CONCLUSION} ký tự.`;
    if (notes.trim().length > MAX_NOTES) return `Ghi chú lâm sàng tối đa ${MAX_NOTES} ký tự.`;
    if (includePlan) {
      if (!plan || plan.items.length === 0) return "Kế hoạch đang trống. Thêm mục từ gợi ý guideline hoặc bỏ chọn lập kế hoạch.";
      const bad = plan.items.findIndex((i) => !i.method.trim() || !isValidInterval(i.interval_months));
      if (bad >= 0) return `Mục ${bad + 1} của kế hoạch cần có phương pháp và chu kỳ là số nguyên tháng (tối thiểu 1).`;
      if (plan.items.some((i) => i.sources.length === 0)) return "Mỗi mục kế hoạch phải có ít nhất một nguồn guideline.";
    }
    return null;
  }

  function requestFinalize() {
    const problem = validate();
    setFormError(problem ?? "");
    if (!problem) setConfirming(true);
  }

  async function finalize() {
    if (!enc) return;
    const base = { conclusion: conclusion.trim(), clinical_notes: notes.trim() || undefined };
    let body: FinalizeEncounterIn;
    if (!includePlan) body = { ...base, final_plan: null, use_draft: false };
    else if (enc.draft_plan && !dirty) body = { ...base, use_draft: true };
    else body = { ...base, final_plan: plan };
    setFinalizing(true);
    setFormError("");
    try {
      const updated = await api.finalizeEncounter(enc.id, body);
      applyEncounter(updated, false);
      loadRecord(updated.patient_id);
      setConfirming(false);
    } catch (err) {
      setConfirming(false);
      if (isStatus(err, 409)) load();
      setFormError(errorMessage(err, "Chưa hoàn tất được lượt khám."));
    } finally {
      setFinalizing(false);
    }
  }

  const back = (
    <Link href="/doctor" className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-indigo-700">
      <ArrowLeft className="h-4 w-4" aria-hidden="true" />
      Về hàng chờ
    </Link>
  );

  if (notFound) {
    return (
      <div className="space-y-4">
        {back}
        <div className="card-padded">
          <EmptyState
            icon={ClipboardCheck}
            title="Không tìm thấy lượt khám"
            action={
              <Link href="/doctor" className="btn-doctor">
                Về hàng chờ
              </Link>
            }
          />
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="space-y-4">
        {back}
        <InlineError message={error} onRetry={load} />
      </div>
    );
  }
  if (!enc) {
    return (
      <div className="space-y-4">
        {back}
        <SkeletonList rows={4} height="h-32" />
      </div>
    );
  }

  const brief = enc.brief;

  return (
    <div className="space-y-6">
      {back}
      <header className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="page-title">{enc.patient_name}</h1>
            <EncounterStatusBadge status={enc.status} />
            {appointment && <PriorityBadge priority={appointment.priority} />}
          </div>
          <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm text-slate-600">
            {appointment && <span>{appointment.service_name}</span>}
            {appointment && <MetaDivider />}
            <span>Bắt đầu {formatDateTime(enc.created_at)}</span>
            {enc.doctor && (
              <>
                <MetaDivider />
                <span>{enc.doctor.full_name}</span>
              </>
            )}
          </p>
          {appointment?.reason && <p className="max-w-prose text-sm text-slate-700">Lý do khám: {appointment.reason}</p>}
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Link href={`/doctor/patients/${enc.patient_id}`} className="btn-secondary">
            <UserCircle className="h-4 w-4" aria-hidden="true" />
            Hồ sơ đầy đủ
          </Link>
          {!finalized && (
            <button
              type="button"
              className="btn-secondary"
              onClick={requestRegenerate}
              disabled={regenerating || confirmRegenerate}
            >
              {regenerating ? <span className="spinner" aria-hidden="true" /> : <RefreshCw className="h-4 w-4" aria-hidden="true" />}
              {regenerating ? "Đang tạo lại…" : "Tạo lại tóm tắt"}
            </button>
          )}
        </div>
      </header>

      {confirmRegenerate && !finalized && (
        <div className="space-y-3 rounded-lg border border-amber-200 bg-amber-50 p-4" role="alertdialog" aria-labelledby="regen-title">
          <p id="regen-title" className="text-sm font-semibold text-amber-950">
            Tạo lại tóm tắt và bỏ các chỉnh sửa kế hoạch?
          </p>
          <p className="text-sm text-amber-900">
            Kế hoạch nháp sẽ được thay bằng bản mới theo tóm tắt mới; những gì bạn đã sửa trong kế hoạch (phương pháp, chu kỳ,
            ngày hẹn, lý do, mục thêm hoặc bỏ) sẽ mất. Kết luận và ghi chú lâm sàng đang soạn được giữ nguyên.
          </p>
          <div className="flex flex-col gap-2 sm:flex-row">
            <button type="button" className="btn-doctor" onClick={() => void regenerate()} disabled={regenerating}>
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              Tạo lại và bỏ chỉnh sửa
            </button>
            <button type="button" className="btn-ghost" onClick={() => setConfirmRegenerate(false)} disabled={regenerating}>
              Giữ kế hoạch đang sửa
            </button>
          </div>
        </div>
      )}

      <Disclaimer text={brief?.disclaimer ?? enc.disclaimer} variant={brief ? "copilot" : "patient"} />
      {notice && (
        <p role="status" className="flex items-center gap-2 rounded-lg border border-indigo-200 bg-indigo-50 p-3 text-sm text-indigo-900">
          <CheckCircle2 className="h-4 w-4 shrink-0" aria-hidden="true" />
          {notice}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="min-w-0 space-y-6 lg:col-span-2">
          {brief ? (
            <BriefPanel
              brief={brief}
              activeEventIds={highlight}
              onFactClick={setHighlight}
              onAddSuggestion={finalized ? undefined : addSuggestion}
              isPlanned={(s) => Boolean(plan?.items.some((i) => sameItem(i, s)))}
            />
          ) : (
            <section className="card-padded">
              <EmptyState
                icon={Sparkles}
                title="Chưa có tóm tắt Copilot"
                text="Tóm tắt có thể chưa tạo được do lỗi AI. Bạn vẫn có thể khám và kết luận bình thường."
                action={
                  !finalized ? (
                    <button
                      type="button"
                      className="btn-doctor"
                      onClick={requestRegenerate}
                      disabled={regenerating || confirmRegenerate}
                    >
                      <RefreshCw className="h-4 w-4" aria-hidden="true" />
                      Tạo tóm tắt
                    </button>
                  ) : undefined
                }
              />
            </section>
          )}

          {finalized ? (
            <section className="card-padded space-y-5 border-l-4 border-l-emerald-500" aria-labelledby="final-title">
              <h2 id="final-title" className="flex items-center gap-2 text-base font-semibold text-slate-900">
                <ClipboardCheck className="h-5 w-5 text-emerald-600" aria-hidden="true" />
                Đã hoàn tất {formatDateTime(enc.finalized_at)}
              </h2>
              <div>
                <h3 className="text-sm font-semibold text-slate-800">Kết luận gửi bệnh nhân</h3>
                <p className="mt-1 max-w-prose whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{enc.conclusion}</p>
              </div>
              {enc.clinical_notes && (
                <div>
                  <h3 className="text-sm font-semibold text-slate-800">Ghi chú lâm sàng (nội bộ)</h3>
                  <p className="mt-1 max-w-prose whitespace-pre-wrap text-sm leading-relaxed text-slate-700">{enc.clinical_notes}</p>
                </div>
              )}
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-slate-800">Kế hoạch đã duyệt</h3>
                {enc.final_plan && enc.final_plan.items.length > 0 ? (
                  <PlanTable plan={enc.final_plan} tone="doctor" />
                ) : (
                  <p className="text-sm text-slate-600">Không lập kế hoạch tầm soát định kỳ.</p>
                )}
              </div>
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-slate-800">Nhắc lịch đã sinh</h3>
                <ReminderList reminders={enc.reminders} />
              </div>
            </section>
          ) : (
            <>
              <section className="card-padded space-y-4" aria-labelledby="plan-title">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <h2 id="plan-title" className="flex items-center gap-2 text-base font-semibold text-slate-900">
                      <NotebookPen className="h-5 w-5 text-indigo-600" aria-hidden="true" />
                      Kế hoạch tầm soát
                    </h2>
                    <p className="text-sm text-slate-500">
                      Bắt đầu từ bản nháp của Copilot. Mục có ngày hẹn sẽ sinh nhắc lịch cho bệnh nhân.
                    </p>
                  </div>
                  {enc.draft_plan && dirty && (
                    <button
                      type="button"
                      className="btn-ghost text-xs"
                      onClick={() => {
                        setPlan(clonePlan(enc.draft_plan));
                        setIncludePlan(true);
                      }}
                    >
                      <RefreshCw className="h-4 w-4" aria-hidden="true" />
                      Khôi phục bản nháp
                    </button>
                  )}
                </div>
                <label htmlFor="include-plan" className="flex cursor-pointer items-start gap-2.5 text-sm text-slate-800">
                  <input
                    id="include-plan"
                    type="checkbox"
                    checked={includePlan}
                    onChange={(e) => setIncludePlan(e.target.checked)}
                    className="mt-0.5 h-4 w-4 accent-indigo-600"
                  />
                  <span>
                    Lập kế hoạch tầm soát định kỳ cho bệnh nhân
                    <span className="block text-xs text-slate-500">
                      Bỏ chọn nếu lượt khám kết thúc không lập kế hoạch (ví dụ cần làm chẩn đoán trước).
                    </span>
                  </span>
                </label>
                {includePlan &&
                  (plan && plan.items.length > 0 ? (
                    <>
                      <PlanTable plan={plan} editable tone="doctor" onChange={setPlan} />
                      <div>
                        <label htmlFor="plan-advice" className="label">
                          Lời dặn chung trong kế hoạch
                        </label>
                        <textarea
                          id="plan-advice"
                          rows={2}
                          value={plan.general_advice}
                          onChange={(e) => setPlan({ ...plan, general_advice: e.target.value })}
                          className="input resize-y focus:border-indigo-600 focus:ring-indigo-600/20"
                        />
                      </div>
                      <p className="text-xs text-slate-500">
                        {dirty ? "Kế hoạch đã được chỉnh sửa so với bản nháp (sẽ lưu vết chỉnh sửa)." : "Đang dùng nguyên bản nháp của Copilot."}
                      </p>
                    </>
                  ) : (
                    <p className="rounded-lg border border-dashed border-slate-300 p-4 text-sm text-slate-600">
                      Chưa có mục nào. Dùng nút &ldquo;Thêm vào kế hoạch&rdquo; ở phần gợi ý guideline để thêm mục (giữ nguyên
                      nguồn trích dẫn).
                    </p>
                  ))}
              </section>

              <section className="card-padded space-y-4" aria-labelledby="finalize-title">
                <h2 id="finalize-title" className="flex items-center gap-2 text-base font-semibold text-slate-900">
                  <ClipboardCheck className="h-5 w-5 text-indigo-600" aria-hidden="true" />
                  Kết luận và hoàn tất
                </h2>
                <div>
                  <label htmlFor="conclusion" className="label">
                    Kết luận / lời dặn gửi bệnh nhân <span className="text-slate-500">(bắt buộc)</span>
                  </label>
                  <textarea
                    id="conclusion"
                    rows={4}
                    required
                    maxLength={MAX_CONCLUSION}
                    value={conclusion}
                    onChange={(e) => setConclusion(e.target.value)}
                    className="input resize-y focus:border-indigo-600 focus:ring-indigo-600/20"
                    placeholder="Bệnh nhân sẽ đọc nội dung này. Viết rõ ràng, bình tĩnh."
                  />
                </div>
                <div>
                  <label htmlFor="notes" className="label">
                    Ghi chú lâm sàng (chỉ bác sĩ thấy)
                  </label>
                  <textarea
                    id="notes"
                    rows={3}
                    maxLength={MAX_NOTES}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    className="input resize-y focus:border-indigo-600 focus:ring-indigo-600/20"
                  />
                </div>
                {formError && <InlineError message={formError} />}
                {confirming ? (
                  <div className="space-y-3 rounded-lg border border-indigo-200 bg-indigo-50 p-4" role="alertdialog" aria-labelledby="confirm-title">
                    <p id="confirm-title" className="text-sm font-semibold text-indigo-950">
                      Xác nhận hoàn tất lượt khám?
                    </p>
                    <p className="text-sm text-indigo-900">
                      Bệnh nhân sẽ thấy kết luận
                      {includePlan
                        ? ` và kế hoạch ${plan?.items.length ?? 0} mục (${plan?.items.filter((i) => i.next_due).length ?? 0} mục có ngày hẹn sinh nhắc lịch)`
                        : ", không kèm kế hoạch tầm soát"}
                      . Sau khi hoàn tất không thể chỉnh sửa.
                    </p>
                    <div className="flex flex-col gap-2 sm:flex-row">
                      <button type="button" className="btn-doctor" onClick={() => void finalize()} disabled={finalizing}>
                        {finalizing ? (
                          <>
                            <span className="spinner" aria-hidden="true" />
                            Đang xử lý…
                          </>
                        ) : (
                          <>
                            <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                            Xác nhận và gửi bệnh nhân
                          </>
                        )}
                      </button>
                      <button type="button" className="btn-ghost" onClick={() => setConfirming(false)} disabled={finalizing}>
                        Quay lại chỉnh sửa
                      </button>
                    </div>
                  </div>
                ) : (
                  <button type="button" className="btn-doctor" onClick={requestFinalize}>
                    <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                    Duyệt và hoàn tất lượt khám
                  </button>
                )}
              </section>
            </>
          )}

          {brief && (
            <section className="card" aria-labelledby="trace-title">
              <button
                type="button"
                onClick={() => setTraceOpen((v) => !v)}
                aria-expanded={traceOpen}
                aria-controls="trace-panel"
                className="flex w-full cursor-pointer items-center justify-between gap-2 px-5 py-4 text-left"
              >
                <span id="trace-title" className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <Activity className="h-4 w-4 text-slate-500" aria-hidden="true" />
                  Trace tạo tóm tắt
                  <span className="break-all text-xs font-normal text-slate-500">({brief.trace_id})</span>
                </span>
                <ChevronDown className={`h-4 w-4 text-slate-500 transition-transform ${traceOpen ? "rotate-180" : ""}`} aria-hidden="true" />
              </button>
              {traceOpen && (
                <div id="trace-panel" className="border-t border-slate-100 bg-slate-50 p-4">
                  <TraceEvents events={brief.trace_events} />
                </div>
              )}
            </section>
          )}
        </div>

        <aside className="min-w-0 space-y-6" aria-label="Hồ sơ và Copilot">
          <section className="card" aria-labelledby="timeline-title">
            <header className="flex items-center justify-between gap-2 border-b border-slate-200 px-4 py-3">
              <h2 id="timeline-title" className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                <History className="h-4 w-4 text-indigo-600" aria-hidden="true" />
                Dòng thời gian hồ sơ
              </h2>
              {highlight.length > 0 && (
                <button type="button" className="btn-ghost min-h-0 px-2 py-1 text-xs" onClick={() => setHighlight([])}>
                  Bỏ đánh dấu
                </button>
              )}
            </header>
            <div className="max-h-[30rem] overflow-y-auto p-4">
              {recordError && <InlineError message={recordError} onRetry={() => loadRecord(enc.patient_id)} />}
              {!record && !recordError && <SkeletonList rows={4} height="h-12" />}
              {record &&
                (record.timeline.length ? (
                  <RecordTimeline events={record.timeline} highlightIds={highlight} showIds />
                ) : (
                  <p className="text-sm text-slate-500">Hồ sơ chưa có mốc nào.</p>
                ))}
            </div>
            {record?.profile && (
              <p className="border-t border-slate-100 px-4 py-2.5 text-xs text-slate-500">
                Hồ sơ cập nhật {formatDate(record.profile.updated_at)}
              </p>
            )}
          </section>
          <CopilotChat encounterId={enc.id} onRecordClick={(id) => setHighlight([id])} />
        </aside>
      </div>
    </div>
  );
}
