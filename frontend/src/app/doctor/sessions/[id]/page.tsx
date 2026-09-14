"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { ScreeningPlan, SessionOut } from "@/types/api";
import { PlanTable } from "@/components/PlanTable";
import { RedFlagAlert } from "@/components/RedFlagAlert";
import { Disclaimer } from "@/components/Disclaimer";

/**
 * Màn duyệt HITL. TODO(FE): PlanTable editable (sửa method/interval/next_due/rationale), hiển thị answers & risk chi tiết.
 */
export default function DoctorSessionPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [s, setS] = useState<SessionOut | null>(null);
  const [plan, setPlan] = useState<ScreeningPlan | null>(null);
  const [note, setNote] = useState("");

  useEffect(() => {
    api.getSession(params.id).then((x) => { setS(x); setPlan(x.draft_plan); }).catch(console.error);
  }, [params.id]);

  async function act(action: "approve" | "reject") {
    if (action === "reject" && !note) return alert("Từ chối cần ghi lý do");
    await api.review(params.id, { action, final_plan: action === "approve" && plan ? plan : undefined, note: note || undefined });
    router.push("/doctor");
  }

  if (!s) return <p>Đang tải…</p>;
  return (
    <main className="space-y-4">
      <h1 className="text-lg font-semibold">Phiên của {s.patient_name}</h1>
      {s.red_flag?.detected && <RedFlagAlert result={s.red_flag} />}
      {s.risk_assessment && (
        <section className="rounded bg-white p-3 shadow text-sm">
          <h2 className="font-medium">Đánh giá nguy cơ (AI)</h2>
          <p>{s.risk_assessment.overall_summary}</p>
          <ul className="mt-1 list-disc pl-5">
            {s.risk_assessment.factors.map((f) => <li key={f.cancer_type}>{f.cancer_type}: <b>{f.level}</b> — {f.reasons.join(", ")}</li>)}
          </ul>
        </section>
      )}
      {plan && (
        <section className="rounded bg-white p-3 shadow">
          <h2 className="font-medium">Bản nháp khuyến nghị (AI) — bác sĩ có thể chỉnh sửa</h2>
          <PlanTable plan={plan} editable onChange={setPlan} />
        </section>
      )}
      {s.status === "pending_review" && (
        <section className="space-y-2">
          <textarea className="w-full rounded border p-2 text-sm" placeholder="Ghi chú cho bệnh nhân (bắt buộc nếu từ chối)" value={note} onChange={(e) => setNote(e.target.value)} />
          <div className="flex gap-2">
            <button onClick={() => act("approve")} className="rounded bg-green-600 px-4 py-2 text-white">Phê duyệt</button>
            <button onClick={() => act("reject")} className="rounded bg-slate-500 px-4 py-2 text-white">Từ chối</button>
          </div>
        </section>
      )}
      <Disclaimer text={s.disclaimer} />
    </main>
  );
}
