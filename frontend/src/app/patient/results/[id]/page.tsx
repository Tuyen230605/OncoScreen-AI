"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { SessionOut } from "@/types/api";
import { Disclaimer } from "@/components/Disclaimer";
import { RedFlagAlert } from "@/components/RedFlagAlert";
import { PlanTable } from "@/components/PlanTable";
import { SessionStatusBadge } from "@/components/SessionStatusBadge";

/** Màn kết quả — rẽ nhánh theo status. pending_review: poll 10s. */
export default function ResultPage({ params }: { params: { id: string } }) {
  const [s, setS] = useState<SessionOut | null>(null);
  useEffect(() => {
    const load = () => api.getSession(params.id).then(setS).catch(console.error);
    load();
    const t = setInterval(() => { if (s?.status === "pending_review" || !s) load(); }, 10_000);
    return () => clearInterval(t);
  }, [params.id, s?.status, s]);

  if (!s) return <p>Đang tải…</p>;
  return (
    <main className="space-y-4">
      <div className="flex items-center gap-2">
        <h1 className="text-lg font-semibold">Kết quả đánh giá</h1>
        <SessionStatusBadge status={s.status} />
      </div>

      {s.status === "collecting" && <Link href={`/patient/survey?session=${s.id}`} className="underline">Tiếp tục khảo sát →</Link>}
      {s.status === "red_flag" && s.red_flag && <RedFlagAlert result={s.red_flag} />}
      {s.status === "pending_review" && (
        <p className="rounded bg-yellow-50 p-3 text-sm">Bác sĩ đang xem xét bản khuyến nghị. Bạn sẽ nhận kết quả sau khi bác sĩ phê duyệt. (tự động cập nhật mỗi 10s)</p>
      )}
      {s.status === "rejected" && <p className="rounded bg-slate-100 p-3 text-sm">Bác sĩ chưa phê duyệt. Ghi chú: {s.doctor_note}</p>}
      {s.status === "approved" && s.final_plan && (
        <>
          {s.risk_assessment && <p className="text-sm text-slate-700">{s.risk_assessment.overall_summary}</p>}
          <PlanTable plan={s.final_plan} />
          <p className="text-xs text-slate-500">Đã duyệt bởi {s.reviewed_by?.full_name} · {s.reviewed_at && new Date(s.reviewed_at).toLocaleString("vi-VN")}</p>
          {/* TODO(FE): ReminderList + link /patient/education/[type] */}
        </>
      )}

      <Disclaimer text={s.disclaimer} />
    </main>
  );
}
