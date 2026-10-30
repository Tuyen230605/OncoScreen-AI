"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { errorMessage, isStatus } from "@/lib/errors";
import type { AppointmentOut, PatientRecordOut } from "@/types/api";
import { cancerLabel, DEFAULT_DISCLAIMER, GENDER_LABEL } from "@/lib/labels";
import { daysUntil, formatDate, formatDateTime } from "@/lib/format";
import { Disclaimer } from "@/components/Disclaimer";
import { AppointmentStatusBadge, PriorityBadge, ReminderStatusBadge } from "@/components/StatusBadge";
import { EmptyState, InlineError, SectionTitle, SkeletonList } from "@/components/ui";
import {
  AlertTriangle,
  Bell,
  CalendarClock,
  CalendarPlus,
  ChevronRight,
  ClipboardCheck,
  MessageSquare,
  Stethoscope,
  UserCircle,
} from "@/components/icons";

/** Tổng quan bệnh nhân: các bước tiếp theo trong hành trình (lịch hẹn, lượt khám đã có kết luận, nhắc lịch). */
export default function PatientDashboard() {
  const [record, setRecord] = useState<PatientRecordOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [confirmCancel, setConfirmCancel] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState<string | null>(null);
  const [actionError, setActionError] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    api
      .getMyRecord()
      .then(setRecord)
      .catch((err) => setError(errorMessage(err, "Chưa tải được hồ sơ của bạn.")))
      .finally(() => setLoading(false));
  }, []);

  useEffect(load, [load]);

  async function cancel(appt: AppointmentOut) {
    setCancelling(appt.id);
    setActionError("");
    try {
      await api.cancelAppointment(appt.id);
      setConfirmCancel(null);
      load();
    } catch (err) {
      setActionError(errorMessage(err, "Chưa huỷ được lịch hẹn."));
      if (isStatus(err, 409)) {
        // Lịch đã chuyển trạng thái (vd. bác sĩ đã bắt đầu khám): tải lại để hiển thị trạng thái mới nhất
        setConfirmCancel(null);
        load();
      }
    } finally {
      setCancelling(null);
    }
  }

  if (loading && !record) {
    return (
      <div className="space-y-6">
        <div className="skeleton h-28 rounded-xl" />
        <SkeletonList rows={3} height="h-20" />
      </div>
    );
  }
  if (error || !record) {
    return <InlineError message={error || "Chưa tải được hồ sơ."} onRetry={load} />;
  }

  const openAppointments = record.appointments.filter((a) => a.status === "requested" || a.status === "confirmed");
  // Lượt khám đang diễn ra: backend không trả encounter chưa hoàn tất cho bệnh nhân (S4) → nhận biết qua lịch hẹn
  // còn mở đã có encounter_id.
  const inExam = openAppointments.filter((a) => a.encounter_id);
  const upcoming = openAppointments
    .filter((a) => !a.encounter_id)
    .sort((a, b) => (a.scheduled_date ?? a.preferred_date).localeCompare(b.scheduled_date ?? b.preferred_date));
  const finalized = record.encounters.filter((e) => e.status === "finalized");
  const dueReminders = record.reminders.filter((r) => r.status === "due");
  const soonReminders = record.reminders
    .filter((r) => r.status === "scheduled" && daysUntil(r.due_date) <= 60)
    .slice(0, 3);
  const serviceOf = (appointmentId: string) =>
    record.appointments.find((a) => a.id === appointmentId)?.service_name ?? "Lượt khám";
  // Phiên tư vấn có dấu hiệu cảnh báo gần nhất (consultations: mới nhất trước). Đặt lịch kèm đúng phiên này thì
  // backend mới xếp ưu tiên; phiên mới nhất có thể không có red-flag.
  const redFlagConsult = record.consultations.find((c) => c.last_reply?.red_flag.detected) ?? null;
  const hasUrgentBooking = record.appointments.some((a) => a.priority === "urgent" && a.status !== "cancelled");
  const firstName = record.user.full_name.trim().split(/\s+/).pop();

  return (
    <div className="space-y-6">
      <section className="card-padded shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="page-title">Xin chào, {firstName}</h1>
            <p className="page-subtitle">Theo dõi lịch khám, kết luận của bác sĩ và lịch tầm soát định kỳ của bạn.</p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Link href="/patient/book" className="btn-primary">
              <CalendarPlus className="h-4 w-4" aria-hidden="true" />
              Đặt lịch khám
            </Link>
            <Link href="/patient/chat" className="btn-secondary">
              <MessageSquare className="h-4 w-4" aria-hidden="true" />
              Hỏi trợ lý tầm soát
            </Link>
          </div>
        </div>
      </section>

      {redFlagConsult && !hasUrgentBooking && (
        <section role="alert" className="rounded-xl border border-red-200 border-l-4 border-l-red-500 bg-red-50/60 p-4">
          <p className="flex items-start gap-2 text-sm text-red-900">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" aria-hidden="true" />
            <span>
              Bạn từng mô tả dấu hiệu cần được bác sĩ khám sớm. Nếu chưa đi khám, hãy đặt lịch ưu tiên. Khi triệu chứng nặng
              lên đột ngột, gọi cấp cứu{" "}
              <a href="tel:115" className="font-bold underline">
                115
              </a>
              .
            </span>
          </p>
          <Link href={`/patient/book?consult=${encodeURIComponent(redFlagConsult.id)}`} className="btn-danger mt-3">
            <CalendarPlus className="h-4 w-4" aria-hidden="true" />
            Đặt lịch ưu tiên
          </Link>
        </section>
      )}

      {dueReminders.length > 0 && (
        <section className="rounded-xl border border-amber-200 border-l-4 border-l-amber-500 bg-amber-50/60 p-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="flex items-start gap-2 text-sm text-amber-900">
              <Bell className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span>
                Bạn có <strong>{dueReminders.length}</strong> mục tầm soát đã đến hạn theo kế hoạch bác sĩ duyệt:{" "}
                {dueReminders.map((r) => r.method).join(", ")}.
              </span>
            </p>
            <Link href="/patient/reminders" className="btn-secondary shrink-0">
              Xem nhắc lịch
            </Link>
          </div>
        </section>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="card-padded" aria-label="Lịch hẹn sắp tới">
          <SectionTitle icon={CalendarClock} title="Lịch hẹn sắp tới" />
          {actionError && (
            <div className="mb-3">
              <InlineError message={actionError} />
            </div>
          )}
          {upcoming.length === 0 && inExam.length === 0 ? (
            <EmptyState
              icon={CalendarClock}
              title="Chưa có lịch hẹn"
              text="Trò chuyện với trợ lý để biết bạn nên tầm soát gì, hoặc đặt lịch tư vấn với bác sĩ."
              action={
                <Link href="/patient/book" className="btn-primary">
                  Đặt lịch khám
                </Link>
              }
            />
          ) : (
            <ul className="space-y-3">
              {inExam.map((a) => (
                <li key={a.id} className="rounded-lg border border-indigo-200 bg-indigo-50/60 p-3.5 text-sm">
                  <p className="flex items-center gap-2 font-semibold text-slate-900">
                    <Stethoscope className="h-4 w-4 text-indigo-600" aria-hidden="true" />
                    {a.service_name}
                  </p>
                  <p className="mt-1 text-slate-600">
                    Bác sĩ đang khám và hoàn tất kết luận. Bạn sẽ thấy kết quả ngay khi bác sĩ duyệt.
                  </p>
                </li>
              ))}
              {upcoming.map((a) => (
                <li key={a.id} className="space-y-2 rounded-lg border border-slate-200 p-3.5 text-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-semibold text-slate-900">{a.service_name}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {a.priority === "urgent" && <PriorityBadge priority="urgent" />}
                      <AppointmentStatusBadge status={a.status} />
                    </div>
                  </div>
                  <p className="text-slate-600">
                    {a.scheduled_date ? (
                      <>
                        Lịch khám: <strong className="text-slate-900">{formatDate(a.scheduled_date)}</strong>
                      </>
                    ) : (
                      <>
                        Ngày mong muốn: <strong className="text-slate-900">{formatDate(a.preferred_date)}</strong>, bệnh viện
                        sẽ xác nhận lịch.
                      </>
                    )}
                  </p>
                  {!a.encounter_id &&
                    (confirmCancel === a.id ? (
                      <div className="flex flex-wrap items-center gap-2 rounded-md bg-slate-50 p-2">
                        <span className="text-slate-700">Huỷ lịch hẹn này?</span>
                        <button
                          type="button"
                          className="btn-secondary min-h-[36px] text-xs"
                          onClick={() => void cancel(a)}
                          disabled={cancelling === a.id}
                        >
                          {cancelling === a.id ? "Đang huỷ…" : "Xác nhận huỷ"}
                        </button>
                        <button type="button" className="btn-ghost min-h-[36px] text-xs" onClick={() => setConfirmCancel(null)}>
                          Giữ lịch
                        </button>
                      </div>
                    ) : (
                      <button
                        type="button"
                        className="btn-ghost min-h-[36px] px-2 text-xs text-slate-500"
                        onClick={() => setConfirmCancel(a.id)}
                      >
                        Huỷ lịch
                      </button>
                    ))}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card-padded" aria-label="Kết luận của bác sĩ">
          <SectionTitle icon={ClipboardCheck} title="Kết luận của bác sĩ" subtitle="Các lượt khám đã được bác sĩ hoàn tất" />
          {finalized.length === 0 ? (
            <EmptyState
              icon={ClipboardCheck}
              title="Chưa có lượt khám hoàn tất"
              text="Sau khi khám, kết luận và kế hoạch tầm soát bác sĩ duyệt sẽ xuất hiện tại đây."
              action={
                <Link href="/patient/record" className="btn-secondary">
                  Xem hồ sơ xuyên suốt
                </Link>
              }
            />
          ) : (
            <ul className="divide-y divide-slate-100">
              {finalized.map((e) => (
                <li key={e.id}>
                  <Link
                    href={`/patient/visits/${e.id}`}
                    className="group flex items-center justify-between gap-3 rounded-lg px-2 py-3 transition-colors hover:bg-slate-50"
                  >
                    <div className="min-w-0">
                      <p className="font-semibold text-slate-900 group-hover:text-teal-700">{serviceOf(e.appointment_id)}</p>
                      <p className="text-xs text-slate-500">
                        Hoàn tất {formatDateTime(e.finalized_at)}
                        {e.doctor ? `, ${e.doctor.full_name}` : ""}
                      </p>
                      {e.final_plan && e.final_plan.items.length > 0 && (
                        <p className="mt-1 truncate text-xs text-slate-600">
                          Kế hoạch: {e.final_plan.items.map((i) => cancerLabel(i.cancer_type)).join(", ")}
                        </p>
                      )}
                    </div>
                    <ChevronRight className="h-4 w-4 shrink-0 text-slate-400 group-hover:text-teal-700" aria-hidden="true" />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card-padded" aria-label="Nhắc lịch sắp tới">
          <SectionTitle
            icon={Bell}
            title="Nhắc lịch tầm soát"
            action={
              <Link href="/patient/reminders" className="text-sm font-semibold text-teal-700 underline-offset-2 hover:underline">
                Xem tất cả
              </Link>
            }
          />
          {dueReminders.length + soonReminders.length === 0 ? (
            <EmptyState
              icon={Bell}
              title="Không có mục nào sắp đến hạn"
              text="Nhắc lịch được tạo từ kế hoạch bác sĩ đã duyệt."
              action={
                <Link href="/patient/reminders" className="btn-secondary">
                  Mở trang nhắc lịch
                </Link>
              }
            />
          ) : (
            <ul className="space-y-2">
              {[...dueReminders, ...soonReminders].map((r) => (
                <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 p-3 text-sm">
                  <div className="min-w-0">
                    <p className="font-medium text-slate-900">{r.method}</p>
                    <p className="text-xs text-slate-500">
                      {cancerLabel(r.cancer_type)}, hạn {formatDate(r.due_date)}
                    </p>
                  </div>
                  <ReminderStatusBadge status={r.status} />
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card-padded" aria-label="Thông tin sức khoẻ">
          <SectionTitle
            icon={UserCircle}
            title="Thông tin sức khoẻ cơ bản"
            action={
              <Link href="/patient/profile" className="text-sm font-semibold text-teal-700 underline-offset-2 hover:underline">
                Cập nhật
              </Link>
            }
          />
          {record.profile ? (
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <dt className="text-xs text-slate-500">Tuổi</dt>
                <dd className="font-semibold text-slate-900">{record.profile.age}</dd>
              </div>
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <dt className="text-xs text-slate-500">Giới tính</dt>
                <dd className="font-semibold text-slate-900">{GENDER_LABEL[record.profile.gender]}</dd>
              </div>
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <dt className="text-xs text-slate-500">Tiền sử gia đình</dt>
                <dd className="font-semibold text-slate-900">
                  {record.profile.genetics_history.length ? `${record.profile.genetics_history.length} ghi nhận` : "Không ghi nhận"}
                </dd>
              </div>
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <dt className="text-xs text-slate-500">Hút thuốc</dt>
                <dd className="font-semibold text-slate-900">
                  {record.profile.lifestyle.smoking === true
                    ? record.profile.lifestyle.pack_years
                      ? `${record.profile.lifestyle.pack_years} gói-năm`
                      : "Có"
                    : record.profile.lifestyle.smoking === false
                      ? "Không"
                      : "Chưa ghi"}
                </dd>
              </div>
            </dl>
          ) : (
            <EmptyState
              icon={UserCircle}
              title="Chưa có thông tin sức khoẻ"
              text="Bổ sung tuổi, giới và tiền sử gia đình để bác sĩ chuẩn bị tốt hơn cho buổi khám."
              action={
                <Link href="/patient/profile" className="btn-primary">
                  Bổ sung thông tin
                </Link>
              }
            />
          )}
        </section>
      </div>

      <Disclaimer text={DEFAULT_DISCLAIMER} compact />
    </div>
  );
}
