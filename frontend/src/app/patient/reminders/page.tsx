"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ReminderOut } from "@/types/api";

const STATUS_LABEL: Record<string, string> = {
  scheduled: "Sắp tới",
  due: "Đến hạn",
  done: "Đã hoàn thành",
  skipped: "Đã bỏ qua",
};

const STATUS_STYLE: Record<string, string> = {
  scheduled: "bg-blue-50 border-blue-100",
  due: "bg-yellow-50 border-yellow-200",
  done: "bg-green-50 border-green-100",
  skipped: "bg-slate-50 border-slate-200",
};

const BADGE_STYLE: Record<string, string> = {
  scheduled: "bg-blue-100 text-blue-700",
  due: "bg-yellow-200 text-yellow-800",
  done: "bg-green-100 text-green-700",
  skipped: "bg-slate-100 text-slate-500",
};

/** Màn lịch nhắc — nhóm theo trạng thái, có nút Đã tầm soát và lọc theo trạng thái. */
export default function RemindersPage() {
  const [items, setItems] = useState<ReminderOut[]>([]);
  const [filter, setFilter] = useState<"all" | "scheduled" | "due" | "done">("all");
  const [completing, setCompleting] = useState<string | null>(null);

  function load() {
    api.listReminders().then(setItems).catch(console.error);
  }

  useEffect(() => { load(); }, []);

  async function handleComplete(id: string) {
    try {
      setCompleting(id);
      await api.completeReminder(id);
      load();
    } finally {
      setCompleting(null);
    }
  }

  const filtered = filter === "all" ? items : items.filter((r) => r.status === filter);

  const counts = {
    all: items.length,
    scheduled: items.filter((r) => r.status === "scheduled").length,
    due: items.filter((r) => r.status === "due").length,
    done: items.filter((r) => r.status === "done").length,
  };

  return (
    <div className="fade-in mx-auto max-w-2xl space-y-6">
      {/* Header */}
      <header>
        <h1 className="page-title">🔔 Lịch nhắc tầm soát</h1>
        <p className="page-subtitle">Theo dõi và cập nhật các buổi tầm soát đã được bác sĩ lên kế hoạch.</p>
      </header>

      {/* Filter tabs */}
      <div className="flex gap-1 rounded-lg bg-slate-100 p-1" role="tablist" aria-label="Lọc theo trạng thái">
        {(["all", "due", "scheduled", "done"] as const).map((tab) => (
          <button
            key={tab}
            role="tab"
            aria-selected={filter === tab}
            onClick={() => setFilter(tab)}
            className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-all ${
              filter === tab
                ? "bg-white shadow text-slate-900"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            {tab === "all" ? "Tất cả" : tab === "due" ? "Đến hạn" : tab === "scheduled" ? "Sắp tới" : "Đã làm"}
            {" "}
            <span className={`ml-0.5 rounded-full px-1.5 py-0.5 text-[10px] ${
              filter === tab ? "bg-slate-100 text-slate-600" : "bg-slate-200 text-slate-500"
            }`}>
              {counts[tab]}
            </span>
          </button>
        ))}
      </div>

      {/* List */}
      {filtered.length === 0 ? (
        <div className="card-padded py-12 text-center">
          <p className="text-2xl mb-2">📅</p>
          <p className="text-sm text-slate-500">
            {filter === "all"
              ? "Chưa có lịch nhắc nào. Bác sĩ sẽ tạo lịch sau khi phê duyệt kế hoạch tầm soát."
              : `Không có lịch nhắc nào ở trạng thái "${STATUS_LABEL[filter] ?? filter}".`}
          </p>
        </div>
      ) : (
        <ul className="space-y-3">
          {filtered.map((r) => (
            <li
              key={r.id}
              className={`card border rounded-xl p-4 transition-all ${STATUS_STYLE[r.status] ?? "bg-white border-slate-200"}`}
            >
              <div className="flex items-start justify-between gap-3">
                {/* Info */}
                <div className="flex-1 space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-semibold text-slate-800">{r.method}</span>
                    <span className={`badge ${BADGE_STYLE[r.status] ?? ""}`}>
                      {STATUS_LABEL[r.status] ?? r.status}
                    </span>
                    {r.status === "due" && (
                      <span className="badge bg-red-100 text-red-700">⚡ Đến hạn rồi!</span>
                    )}
                  </div>
                  <p className="text-xs text-slate-600">
                    Loại: <strong>{r.cancer_type}</strong>
                    {" · "}
                    Ngày: <strong>{r.due_date}</strong>
                  </p>
                  {r.message && (
                    <p className="text-xs text-slate-500 italic">{r.message}</p>
                  )}
                  {r.completed_at && (
                    <p className="text-xs text-green-600">
                      ✓ Đã hoàn thành: {new Date(r.completed_at).toLocaleDateString("vi-VN")}
                    </p>
                  )}
                </div>

                {/* Action */}
                {r.status !== "done" && r.status !== "skipped" && (
                  <button
                    onClick={() => handleComplete(r.id)}
                    disabled={completing === r.id}
                    className="btn-secondary shrink-0 text-xs"
                  >
                    {completing === r.id ? (
                      <span className="spinner h-3 w-3" />
                    ) : (
                      "✓ Đã tầm soát"
                    )}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      {/* Info note */}
      <p className="text-xs text-center text-slate-400">
        Lịch nhắc được tạo tự động sau khi bác sĩ phê duyệt kế hoạch tầm soát.
      </p>
    </div>
  );
}
