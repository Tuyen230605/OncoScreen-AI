"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { SessionStatus, SessionSummary } from "@/types/api";
import { SessionStatusBadge } from "@/components/SessionStatusBadge";

/** Dashboard bác sĩ: hàng chờ duyệt mặc định. TODO(FE): tab, phân trang, tìm bệnh nhân. */
export default function DoctorDashboard() {
  const [status, setStatus] = useState<SessionStatus | "">("pending_review");
  const [items, setItems] = useState<SessionSummary[]>([]);
  useEffect(() => {
    api.listAllSessions(status || undefined).then((p) => setItems(p.items)).catch(console.error);
  }, [status]);
  return (
    <main className="space-y-3">
      <div className="flex items-center gap-2">
        <h1 className="text-lg font-semibold">Hàng chờ duyệt</h1>
        <select className="rounded border p-1 text-sm" value={status} onChange={(e) => setStatus(e.target.value as SessionStatus | "")}>
          <option value="pending_review">Chờ duyệt</option>
          <option value="red_flag">Khẩn (red-flag)</option>
          <option value="approved">Đã duyệt</option>
          <option value="">Tất cả</option>
        </select>
      </div>
      <ul className="divide-y rounded bg-white shadow">
        {items.map((s) => (
          <li key={s.id} className="flex items-center justify-between p-3 text-sm">
            <Link href={`/doctor/sessions/${s.id}`} className="underline">{s.patient_name}</Link>
            <span className="flex items-center gap-2">
              {s.has_red_flag && <span className="rounded bg-red-600 px-2 text-xs text-white">KHẨN</span>}
              <SessionStatusBadge status={s.status} />
            </span>
          </li>
        ))}
      </ul>
    </main>
  );
}
