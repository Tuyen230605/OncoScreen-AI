"use client";
import { useState } from "react";
import type { PlanItem, ScreeningPlan } from "@/types/api";

/**
 * Bảng kế hoạch tầm soát.
 * - readonly (patient): chỉ hiện thông tin.
 * - editable (doctor): inline input cho method, interval_months, next_due, rationale; gọi onChange khi thay đổi.
 */
export function PlanTable({
  plan,
  editable = false,
  onChange,
}: {
  plan: ScreeningPlan;
  editable?: boolean;
  onChange?: (p: ScreeningPlan) => void;
}) {
  const [items, setItems] = useState<PlanItem[]>(plan.items);

  function updateItem(index: number, patch: Partial<PlanItem>) {
    const next = items.map((it, i) => (i === index ? { ...it, ...patch } : it));
    setItems(next);
    onChange?.({ ...plan, items: next });
  }

  return (
    <div className="space-y-4">
      {/* Desktop table */}
      <div className="overflow-x-auto hidden md:block">
        <table className="w-full text-sm border-collapse">
          <thead className="bg-slate-50 text-left">
            <tr>
              <th className="p-2 font-semibold text-slate-700">Loại</th>
              <th className="p-2 font-semibold text-slate-700">Phương pháp</th>
              <th className="p-2 font-semibold text-slate-700">Chu kỳ</th>
              <th className="p-2 font-semibold text-slate-700">Lần tới</th>
              <th className="p-2 font-semibold text-slate-700">Lý do &amp; nguồn</th>
            </tr>
          </thead>
          <tbody>
            {items.map((it, i) => (
              <tr key={i} className="border-t align-top hover:bg-slate-50/50">
                {/* Cancer type — read only */}
                <td className="p-2">
                  <span className="inline-block rounded bg-blue-50 px-2 py-0.5 text-xs font-semibold uppercase text-blue-700">
                    {it.cancer_type}
                  </span>
                </td>

                {/* Method */}
                <td className="p-2">
                  {editable ? (
                    <input
                      id={`plan-method-${i}`}
                      type="text"
                      value={it.method}
                      onChange={(e) => updateItem(i, { method: e.target.value })}
                      className="input text-sm w-full"
                    />
                  ) : (
                    it.method
                  )}
                </td>

                {/* Interval */}
                <td className="p-2">
                  {editable ? (
                    <div className="flex items-center gap-1">
                      <input
                        id={`plan-interval-${i}`}
                        type="number"
                        min={1}
                        value={it.interval_months}
                        onChange={(e) => updateItem(i, { interval_months: Number(e.target.value) })}
                        className="input text-sm w-20"
                      />
                      <span className="text-slate-500 text-xs">tháng</span>
                    </div>
                  ) : (
                    `${it.interval_months} tháng`
                  )}
                </td>

                {/* Next due */}
                <td className="p-2">
                  {editable ? (
                    <input
                      id={`plan-next-due-${i}`}
                      type="date"
                      value={it.next_due}
                      onChange={(e) => updateItem(i, { next_due: e.target.value })}
                      className="input text-sm"
                    />
                  ) : (
                    it.next_due
                  )}
                </td>

                {/* Rationale + Sources */}
                <td className="p-2 max-w-xs">
                  {editable ? (
                    <textarea
                      id={`plan-rationale-${i}`}
                      rows={3}
                      value={it.rationale}
                      onChange={(e) => updateItem(i, { rationale: e.target.value })}
                      className="input text-sm w-full resize-y"
                    />
                  ) : (
                    <p>{it.rationale}</p>
                  )}
                  <ul className="mt-1 text-xs text-slate-500 space-y-0.5">
                    {it.sources.map((s) => (
                      <li key={s.doc_id}>
                        📄{" "}
                        {s.url ? (
                          <a className="underline" href={s.url} target="_blank" rel="noreferrer">
                            {s.title}
                          </a>
                        ) : (
                          s.title
                        )}
                        {s.section ? ` · ${s.section}` : ""}
                      </li>
                    ))}
                  </ul>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile card list */}
      <div className="space-y-3 md:hidden">
        {items.map((it, i) => (
          <div key={i} className="rounded-lg border border-slate-200 p-3 space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="rounded bg-blue-50 px-2 py-0.5 text-xs font-semibold uppercase text-blue-700">
                {it.cancer_type}
              </span>
            </div>
            <div>
              <span className="text-xs text-slate-500">Phương pháp: </span>
              {editable ? (
                <input
                  type="text"
                  value={it.method}
                  onChange={(e) => updateItem(i, { method: e.target.value })}
                  className="input text-sm w-full mt-0.5"
                />
              ) : (
                <span>{it.method}</span>
              )}
            </div>
            <div className="flex gap-4">
              <div>
                <span className="text-xs text-slate-500">Chu kỳ: </span>
                {editable ? (
                  <input
                    type="number"
                    min={1}
                    value={it.interval_months}
                    onChange={(e) => updateItem(i, { interval_months: Number(e.target.value) })}
                    className="input text-sm w-20"
                  />
                ) : (
                  <span>{it.interval_months} tháng</span>
                )}
              </div>
              <div>
                <span className="text-xs text-slate-500">Lần tới: </span>
                {editable ? (
                  <input
                    type="date"
                    value={it.next_due}
                    onChange={(e) => updateItem(i, { next_due: e.target.value })}
                    className="input text-sm"
                  />
                ) : (
                  <span>{it.next_due}</span>
                )}
              </div>
            </div>
            <div>
              <span className="text-xs text-slate-500">Lý do: </span>
              {editable ? (
                <textarea
                  rows={2}
                  value={it.rationale}
                  onChange={(e) => updateItem(i, { rationale: e.target.value })}
                  className="input text-sm w-full mt-0.5 resize-y"
                />
              ) : (
                <span>{it.rationale}</span>
              )}
            </div>
            <ul className="text-xs text-slate-500 space-y-0.5">
              {it.sources.map((s) => (
                <li key={s.doc_id}>
                  📄{" "}
                  {s.url ? (
                    <a className="underline" href={s.url} target="_blank" rel="noreferrer">
                      {s.title}
                    </a>
                  ) : (
                    s.title
                  )}
                  {s.section ? ` · ${s.section}` : ""}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {plan.general_advice && (
        <p className="text-sm text-slate-600 italic border-t border-slate-100 pt-3">{plan.general_advice}</p>
      )}
    </div>
  );
}
