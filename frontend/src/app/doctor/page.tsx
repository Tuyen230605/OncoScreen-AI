"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { SessionStatus, SessionSummary } from "@/types/api";
import { SessionStatusBadge } from "@/components/SessionStatusBadge";

/** Dashboard bác sĩ: hàng chờ duyệt với filter theo trạng thái. */
export default function DoctorDashboard() {
  const [status, setStatus] = useState<SessionStatus | "">("");
  const [items, setItems] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .listAllSessions(status || undefined)
      .then((p) => setItems(p.items))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [status]);

  const tabs: { label: string; value: SessionStatus | "" }[] = [
    { label: "Tất cả", value: "" },
    { label: "Chờ duyệt", value: "pending_review" },
    { label: "Khẩn (Red-Flag)", value: "red_flag" },
    { label: "Đã duyệt", value: "approved" },
    { label: "Từ chối", value: "rejected" },
  ];

  return (
    <div className="fade-in space-y-6">
      {/* Header */}
      <div>
        <h1 className="page-title">Hàng chờ duyệt</h1>
        <p className="page-subtitle">Quản lý và phê duyệt kết quả đánh giá nguy cơ của bệnh nhân.</p>
      </div>

      {/* Filter tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-2">
        {tabs.map((t) => (
          <button
            key={t.value}
            id={`tab-${t.value || "all"}`}
            onClick={() => setStatus(t.value)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition-all ${
              status === t.value
                ? "bg-blue-600 text-white shadow-sm"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Session list */}
      {loading ? (
        <div className="flex justify-center py-12">
          <span className="spinner h-6 w-6 text-blue-500" aria-label="Đang tải…" />
        </div>
      ) : items.length === 0 ? (
        <div className="card-padded flex flex-col items-center gap-2 py-12 text-center text-slate-500">
          <span className="text-3xl">📋</span>
          <p className="font-medium">Không có phiên nào</p>
          <p className="text-sm">Không tìm thấy phiên theo trạng thái đã chọn.</p>
        </div>
      ) : (
        <ul className="space-y-2">
          {items.map((s) => (
            <li key={s.id}>
              <Link
                href={`/doctor/sessions/${s.id}`}
                className="card-padded flex items-center justify-between gap-4 transition-shadow hover:shadow-md"
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-800 truncate">{s.patient_name}</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {new Date(s.created_at).toLocaleDateString("vi-VN", {
                      weekday: "short",
                      day: "numeric",
                      month: "long",
                      year: "numeric",
                    })}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {s.has_red_flag && (
                    <span className="rounded-full bg-red-600 px-2.5 py-0.5 text-xs font-semibold text-white">
                      KHẨN
                    </span>
                  )}
                  <SessionStatusBadge status={s.status} />
                  <span className="text-slate-400">›</span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
