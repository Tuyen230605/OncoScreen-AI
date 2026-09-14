import type { ScreeningPlan } from "@/types/api";

/**
 * Bảng kế hoạch tầm soát. readonly cho patient; editable=true cho doctor (TODO(FE): input inline + onChange).
 */
export function PlanTable({ plan, editable = false, onChange }: { plan: ScreeningPlan; editable?: boolean; onChange?: (p: ScreeningPlan) => void }) {
  void editable;
  void onChange;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-slate-100 text-left">
          <tr>
            <th className="p-2">Loại</th>
            <th className="p-2">Phương pháp</th>
            <th className="p-2">Chu kỳ</th>
            <th className="p-2">Lần tới</th>
            <th className="p-2">Lý do & nguồn</th>
          </tr>
        </thead>
        <tbody>
          {plan.items.map((it, i) => (
            <tr key={i} className="border-t align-top">
              <td className="p-2 font-medium">{it.cancer_type}</td>
              <td className="p-2">{it.method}</td>
              <td className="p-2">{it.interval_months} tháng</td>
              <td className="p-2">{it.next_due}</td>
              <td className="p-2">
                <p>{it.rationale}</p>
                <ul className="mt-1 text-xs text-slate-500">
                  {it.sources.map((s) => (
                    <li key={s.doc_id}>
                      📄 {s.url ? <a className="underline" href={s.url} target="_blank" rel="noreferrer">{s.title}</a> : s.title}
                      {s.section ? ` · ${s.section}` : ""}
                    </li>
                  ))}
                </ul>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {plan.general_advice && <p className="mt-2 text-sm text-slate-600">{plan.general_advice}</p>}
    </div>
  );
}
