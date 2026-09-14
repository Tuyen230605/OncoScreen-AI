"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { SessionSummary } from "@/types/api";
import { SessionStatusBadge } from "@/components/SessionStatusBadge";

/** Dashboard bệnh nhân. TODO(FE): hiển thị hồ sơ, reminders sắp tới, link giáo dục. */
export default function PatientDashboard() {
  const router = useRouter();
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  useEffect(() => {
    api.listMySessions().then((p) => setSessions(p.items)).catch(console.error);
  }, []);

  async function start() {
    const s = await api.createSession();
    router.push(`/patient/survey?session=${s.id}`);
  }

  return (
    <main className="space-y-4">
      <div className="flex gap-2">
        <button onClick={start} className="rounded bg-blue-600 px-4 py-2 text-white">Bắt đầu đánh giá nguy cơ</button>
        <Link href="/patient/reminders" className="rounded border px-4 py-2">Lịch nhắc</Link>
      </div>
      <h2 className="font-semibold">Các phiên của bạn</h2>
      <ul className="divide-y rounded bg-white shadow">
        {sessions.map((s) => (
          <li key={s.id} className="flex items-center justify-between p-3">
            <Link href={`/patient/results/${s.id}`} className="underline">{new Date(s.created_at).toLocaleString("vi-VN")}</Link>
            <SessionStatusBadge status={s.status} />
          </li>
        ))}
      </ul>
    </main>
  );
}
