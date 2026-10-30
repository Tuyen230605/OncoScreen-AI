"use client";
import type { PlanItem, ScreeningPlan } from "@/types/api";
import { cancerLabel } from "@/lib/labels";
import { daysUntil, formatDate, intervalLabel, todayISO } from "@/lib/format";
import { SourceList } from "@/components/SourceList";
import { Calendar, Trash2 } from "@/components/icons";

/** `PlanItem.interval_months` ở backend là số nguyên > 0 (nhập 1.5 sẽ bị từ chối). */
export const isValidInterval = (months: number) => Number.isInteger(months) && months >= 1;

/**
 * Bảng kế hoạch tầm soát (controlled).
 * - readonly (bệnh nhân / xem lại): bảng trên md+, thẻ xếp dọc trên mobile.
 * - editable (bác sĩ): sửa phương pháp, chu kỳ, ngày hẹn kế tiếp, lý do; xoá mục. Nguồn giữ nguyên, chỉ đọc.
 */
export function PlanTable({
  plan,
  editable = false,
  onChange,
  tone = "patient",
}: {
  plan: ScreeningPlan;
  editable?: boolean;
  onChange?: (p: ScreeningPlan) => void;
  tone?: "patient" | "doctor";
}) {
  const items = plan.items;

  function updateItem(index: number, patch: Partial<PlanItem>) {
    onChange?.({ ...plan, items: items.map((it, i) => (i === index ? { ...it, ...patch } : it)) });
  }
  function removeItem(index: number) {
    onChange?.({ ...plan, items: items.filter((_, i) => i !== index) });
  }

  const dueSoon = (it: PlanItem) => it.next_due !== null && daysUntil(it.next_due) <= 30;
  const pill =
    tone === "doctor"
      ? "border-indigo-200 bg-indigo-50 text-indigo-800"
      : "border-teal-200 bg-teal-50 text-teal-800";

  if (editable) {
    return (
      <div className="space-y-3">
        {items.map((it, i) => (
          <div
            key={`${it.cancer_type}-${i}`}
            className={`space-y-3 rounded-lg border border-slate-200 bg-white p-4 ${
              it.priority === 1 ? "border-l-4 border-l-indigo-500" : ""
            }`}
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`badge border ${pill}`}>{cancerLabel(it.cancer_type)}</span>
                {it.priority === 1 && <span className="text-xs font-medium text-indigo-700">Ưu tiên</span>}
                {it.start_age !== null && <span className="text-xs text-slate-500">Bắt đầu từ {it.start_age} tuổi</span>}
              </div>
              <button
                type="button"
                onClick={() => removeItem(i)}
                className="btn-ghost min-h-0 px-2 py-1 text-xs text-slate-500 hover:text-red-700"
                aria-label={`Bỏ mục ${cancerLabel(it.cancer_type)} khỏi kế hoạch`}
              >
                <Trash2 className="h-4 w-4" aria-hidden="true" />
                <span>Bỏ mục</span>
              </button>
            </div>

            <div>
              <label htmlFor={`plan-method-${i}`} className="label text-xs">
                Phương pháp
              </label>
              <input
                id={`plan-method-${i}`}
                type="text"
                value={it.method}
                onChange={(e) => updateItem(i, { method: e.target.value })}
                className="input"
              />
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label htmlFor={`plan-interval-${i}`} className="label text-xs">
                  Chu kỳ (tháng)
                </label>
                <input
                  id={`plan-interval-${i}`}
                  type="number"
                  min={1}
                  step={1}
                  inputMode="numeric"
                  value={it.interval_months > 0 ? it.interval_months : ""}
                  onChange={(e) => updateItem(i, { interval_months: e.target.value === "" ? 0 : Number(e.target.value) })}
                  className={`input ${isValidInterval(it.interval_months) ? "" : "input-error"}`}
                  aria-invalid={!isValidInterval(it.interval_months)}
                  aria-describedby={`plan-interval-hint-${i}`}
                />
                <p id={`plan-interval-hint-${i}`} className="mt-1 text-xs text-slate-500">
                  {isValidInterval(it.interval_months)
                    ? intervalLabel(it.interval_months)
                    : "Bác sĩ cần đặt chu kỳ là số nguyên tháng, tối thiểu 1."}
                </p>
              </div>
              <div>
                <label htmlFor={`plan-next-due-${i}`} className="label text-xs">
                  Ngày hẹn kế tiếp
                </label>
                <input
                  id={`plan-next-due-${i}`}
                  type="date"
                  min={todayISO()}
                  value={it.next_due ?? ""}
                  onChange={(e) => updateItem(i, { next_due: e.target.value || null })}
                  className="input"
                  aria-describedby={`plan-next-due-hint-${i}`}
                />
                <p id={`plan-next-due-hint-${i}`} className="mt-1 text-xs text-slate-500">
                  {it.next_due ? "Sẽ sinh nhắc lịch cho bệnh nhân." : "Để trống: không sinh nhắc lịch."}
                </p>
              </div>
            </div>

            <div>
              <label htmlFor={`plan-rationale-${i}`} className="label text-xs">
                Lý do
              </label>
              <textarea
                id={`plan-rationale-${i}`}
                rows={2}
                value={it.rationale}
                onChange={(e) => updateItem(i, { rationale: e.target.value })}
                className="input resize-y"
              />
            </div>

            <SourceList sources={it.sources} tone="doctor" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Desktop */}
      <div className="hidden overflow-x-auto rounded-xl border border-slate-200 bg-white md:block">
        <table className="w-full border-collapse text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-left">
            <tr>
              <th scope="col" className="px-4 py-3 font-semibold text-slate-700">
                Loại ung thư
              </th>
              <th scope="col" className="px-4 py-3 font-semibold text-slate-700">
                Phương pháp
              </th>
              <th scope="col" className="px-4 py-3 font-semibold text-slate-700">
                Chu kỳ
              </th>
              <th scope="col" className="px-4 py-3 font-semibold text-slate-700">
                Lần tới
              </th>
              <th scope="col" className="px-4 py-3 font-semibold text-slate-700">
                Lý do và nguồn
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {items.map((it, i) => (
              <tr
                key={`${it.cancer_type}-${i}`}
                className={`align-top ${dueSoon(it) ? "bg-amber-50" : ""} ${
                  it.priority === 1 ? (tone === "doctor" ? "border-l-4 border-l-indigo-500" : "border-l-4 border-l-teal-500") : ""
                }`}
              >
                <td className="whitespace-nowrap px-4 py-3.5">
                  <span className={`badge border ${pill}`}>{cancerLabel(it.cancer_type)}</span>
                </td>
                <td className="px-4 py-3.5 font-semibold text-slate-900">{it.method}</td>
                <td className="whitespace-nowrap px-4 py-3.5 text-slate-700">{intervalLabel(it.interval_months)}</td>
                <td className="whitespace-nowrap px-4 py-3.5">
                  <span className={`inline-flex items-center gap-1 font-medium ${it.next_due ? "text-slate-800" : "text-slate-400"}`}>
                    <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
                    {formatDate(it.next_due)}
                  </span>
                  {dueSoon(it) && <p className="mt-0.5 text-xs font-medium text-amber-800">Sắp đến hạn</p>}
                </td>
                <td className="max-w-sm space-y-2 px-4 py-3.5">
                  <p className="text-xs leading-relaxed text-slate-700">{it.rationale}</p>
                  <SourceList sources={it.sources} tone={tone} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile */}
      <div className="space-y-3 md:hidden">
        {items.map((it, i) => (
          <div
            key={`${it.cancer_type}-${i}`}
            className={`space-y-3 rounded-lg border border-slate-200 p-4 text-sm ${dueSoon(it) ? "bg-amber-50" : "bg-white"} ${
              it.priority === 1 ? (tone === "doctor" ? "border-l-4 border-l-indigo-500" : "border-l-4 border-l-teal-500") : ""
            }`}
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className={`badge border ${pill}`}>{cancerLabel(it.cancer_type)}</span>
              <span className="text-xs text-slate-500">{intervalLabel(it.interval_months)}</span>
            </div>
            <p className="font-semibold text-slate-900">{it.method}</p>
            <p className="flex items-center gap-1 text-xs text-slate-600">
              <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
              Lần tới: <strong className="font-semibold text-slate-800">{formatDate(it.next_due)}</strong>
              {dueSoon(it) && <span className="ml-1 font-medium text-amber-800">(sắp đến hạn)</span>}
            </p>
            <p className="text-xs leading-relaxed text-slate-700">{it.rationale}</p>
            <SourceList sources={it.sources} tone={tone} />
          </div>
        ))}
      </div>

      {plan.general_advice && (
        <p className="rounded-lg border border-slate-200 bg-slate-50 p-3.5 text-sm leading-relaxed text-slate-600">
          <strong className="mr-1 text-slate-700">Lời dặn chung:</strong>
          {plan.general_advice}
        </p>
      )}
    </div>
  );
}
