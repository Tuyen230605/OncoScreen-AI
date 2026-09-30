"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { PatientProfileOut, ReminderOut, SessionSummary } from "@/types/api";
import { SessionStatusBadge } from "@/components/SessionStatusBadge";

const GENDER_LABEL: Record<string, string> = {
  female: "Nữ",
  male: "Nam",
  other: "Khác",
};

/** Dashboard bệnh nhân — Tuần 2: hiển thị profile, reminder sắp tới, danh sách phiên, link hành động. */
export default function PatientDashboard() {
  const router = useRouter();
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [profile, setProfile] = useState<PatientProfileOut | null>(null);
  const [reminders, setReminders] = useState<ReminderOut[]>([]);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    api.listMySessions().then((p) => setSessions(p.items)).catch(console.error);
    api.getProfile().then(setProfile).catch(() => null);
    api.listReminders().then(setReminders).catch(console.error);
  }, []);

  async function start() {
    try {
      setStarting(true);
      const s = await api.createSession();
      router.push(`/patient/survey?session=${s.id}`);
    } catch {
      setStarting(false);
    }
  }

  // Reminder sắp tới: lấy 3 cái scheduled/due gần nhất
  const upcomingReminders = reminders
    .filter((r) => r.status === "scheduled" || r.status === "due")
    .slice(0, 3);

  return (
    <div className="fade-in space-y-6">
      {/* ===== Hero / Quick Actions ===== */}
      <section className="card-padded flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="page-title">Tổng quan</h1>
          <p className="page-subtitle">Quản lý lịch tầm soát và kết quả đánh giá của bạn.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            id="btn-start-survey"
            onClick={start}
            disabled={starting}
            className="btn-primary"
          >
            {starting ? <span className="spinner h-4 w-4" /> : "＋"}
            {starting ? "Đang tạo…" : "Bắt đầu đánh giá nguy cơ"}
          </button>
          <Link href="/patient/profile" className="btn-secondary">
            ✏️ Cập nhật hồ sơ
          </Link>
          <Link href="/patient/reminders" className="btn-secondary">
            🔔 Lịch nhắc
          </Link>
        </div>
      </section>

      {/* ===== Profile summary ===== */}
      {profile ? (
        <section className="card-padded">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-slate-800">Hồ sơ sức khỏe</h2>
            <Link href="/patient/profile" className="text-xs text-blue-600 hover:underline">
              Chỉnh sửa →
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
            <div className="rounded-lg bg-slate-50 p-3">
              <p className="text-xs text-slate-500">Tuổi</p>
              <p className="font-medium text-slate-800">{profile.age}</p>
            </div>
            <div className="rounded-lg bg-slate-50 p-3">
              <p className="text-xs text-slate-500">Giới tính</p>
              <p className="font-medium text-slate-800">{GENDER_LABEL[profile.gender] ?? profile.gender}</p>
            </div>
            <div className="rounded-lg bg-slate-50 p-3">
              <p className="text-xs text-slate-500">Tiền sử gia đình</p>
              <p className="font-medium text-slate-800">
                {profile.genetics_history.length > 0
                  ? `${profile.genetics_history.length} mục`
                  : "Chưa có"}
              </p>
            </div>
            <div className="rounded-lg bg-slate-50 p-3">
              <p className="text-xs text-slate-500">Hút thuốc</p>
              <p className="font-medium text-slate-800">
                {profile.lifestyle?.smoking === true
                  ? `Có${profile.lifestyle.pack_years ? ` (${profile.lifestyle.pack_years} gói-năm)` : ""}`
                  : profile.lifestyle?.smoking === false
                  ? "Không"
                  : "—"}
              </p>
            </div>
          </div>
        </section>
      ) : (
        <section className="card-padded">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-700">Hồ sơ sức khỏe chưa được tạo</p>
              <p className="text-xs text-slate-500 mt-0.5">Cập nhật hồ sơ để nhận gợi ý tầm soát chính xác hơn.</p>
            </div>
            <Link href="/patient/profile" className="btn-primary">
              Tạo hồ sơ ngay
            </Link>
          </div>
        </section>
      )}

      {/* ===== Upcoming reminders ===== */}
      {upcomingReminders.length > 0 && (
        <section className="card-padded">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-slate-800">🔔 Nhắc lịch sắp tới</h2>
            <Link href="/patient/reminders" className="text-xs text-blue-600 hover:underline">
              Xem tất cả →
            </Link>
          </div>
          <ul className="space-y-2">
            {upcomingReminders.map((r) => (
              <li
                key={r.id}
                className={`flex items-center justify-between rounded-lg p-3 text-sm ${
                  r.status === "due" ? "bg-yellow-50 border border-yellow-200" : "bg-blue-50 border border-blue-100"
                }`}
              >
                <div>
                  <span className="font-medium text-slate-800">{r.method}</span>
                  <span className="mx-2 text-slate-400">·</span>
                  <span className="text-slate-600">{r.cancer_type}</span>
                </div>
                <div className="text-right">
                  {r.status === "due" && (
                    <span className="badge bg-yellow-200 text-yellow-800 mb-0.5">Đến hạn</span>
                  )}
                  <p className="text-xs text-slate-500">{r.due_date}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* ===== Sessions list ===== */}
      <section className="card-padded">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-slate-800">Lịch sử đánh giá</h2>
          <span className="text-xs text-slate-500">{sessions.length} phiên</span>
        </div>

        {sessions.length === 0 ? (
          <div className="py-10 text-center">
            <p className="text-sm text-slate-500">Bạn chưa có phiên đánh giá nào.</p>
            <button onClick={start} disabled={starting} className="btn-primary mt-4">
              Bắt đầu đánh giá đầu tiên
            </button>
          </div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {sessions.map((s) => (
              <li key={s.id}>
                <Link
                  href={`/patient/results/${s.id}`}
                  className="flex items-center justify-between py-3 px-1 rounded-lg transition-colors hover:bg-slate-50"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-800">
                      {new Date(s.created_at).toLocaleDateString("vi-VN", {
                        weekday: "short",
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                      })}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {new Date(s.created_at).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {s.has_red_flag && (
                      <span className="badge bg-red-100 text-red-700">KHẨN</span>
                    )}
                    <SessionStatusBadge status={s.status} />
                    <span className="text-slate-400">›</span>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
