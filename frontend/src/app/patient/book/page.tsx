"use client";
import Link from "next/link";
import { FormEvent, Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { getUser } from "@/lib/auth";
import { anonymousConsultToken, clearConsult, saveConsult } from "@/lib/consult";
import { errorMessage } from "@/lib/errors";
import { cancerLabel, DEFAULT_DISCLAIMER } from "@/lib/labels";
import { formatDate, todayISO } from "@/lib/format";
import type { AppointmentOut, ConsultationOut, ServiceOut } from "@/types/api";
import { Disclaimer } from "@/components/Disclaimer";
import { RedFlagAlert } from "@/components/RedFlagAlert";
import { AppointmentStatusBadge, PriorityBadge } from "@/components/StatusBadge";
import { InlineError, SkeletonList } from "@/components/ui";
import { CalendarCheck, CalendarPlus, CheckCircle2, Info, LayoutDashboard, MessageSquare, Sparkles } from "@/components/icons";

const MAX_OPEN = 3;

function BookingForm() {
  const params = useSearchParams();
  const consultId = params.get("consult");

  const [services, setServices] = useState<ServiceOut[]>([]);
  const [consult, setConsult] = useState<ConsultationOut | null>(null);
  const [consultNote, setConsultNote] = useState("");
  const [openCount, setOpenCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [selected, setSelected] = useState<string[]>([]);
  const [date, setDate] = useState("");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [created, setCreated] = useState<AppointmentOut[]>([]);

  useEffect(() => {
    let cancelled = false;
    async function loadConsult(id: string): Promise<ConsultationOut | null> {
      try {
        return await api.getConsultation(id);
      } catch {
        // Phiên ẩn danh chưa gắn tài khoản: thử gắn bằng token đang lưu trên trình duyệt
        const token = anonymousConsultToken(id);
        if (!token) return null;
        try {
          const claimed = await api.claimConsultation(id, token);
          // Phiên giờ thuộc tài khoản: /patient/chat tiếp tục đúng cuộc trò chuyện này
          const owner = getUser();
          if (owner) saveConsult({ id, access_token: token }, owner.id);
          clearConsult(null);
          return claimed;
        } catch {
          return null;
        }
      }
    }
    async function load() {
      setLoading(true);
      setLoadError("");
      try {
        const [svc, mine, c] = await Promise.all([
          api.listServices(),
          api.listMyAppointments(),
          consultId ? loadConsult(consultId) : Promise.resolve(null),
        ]);
        if (cancelled) return;
        setServices(svc);
        setOpenCount(mine.filter((a) => a.status === "requested" || a.status === "confirmed").length);
        if (consultId && !c) {
          setConsultNote("Không mở được cuộc trò chuyện đã chọn. Bạn vẫn có thể đặt lịch bình thường.");
        }
        setConsult(c);
        const hint = c?.last_reply?.booking_hint;
        if (hint) {
          setSelected(hint.service_codes.filter((code) => svc.some((s) => s.code === code)).slice(0, MAX_OPEN));
          setReason(hint.reason);
          if (hint.priority === "urgent") setDate(todayISO());
        }
      } catch (err) {
        if (!cancelled) setLoadError(errorMessage(err, "Chưa tải được danh mục dịch vụ."));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [consultId]);

  const hint = consult?.last_reply?.booking_hint ?? null;
  const redFlag = consult?.last_reply?.red_flag.detected ? consult.last_reply.red_flag : null;
  const urgent = Boolean(redFlag) || hint?.priority === "urgent" || selected.includes("oncology_priority");
  const remaining = Math.max(0, MAX_OPEN - openCount);
  // Trang hiển thị cảnh báo / lý do khám do trợ lý soạn → luôn kèm lưu ý y khoa (S6)
  const disclaimer = <Disclaimer text={consult?.last_reply?.disclaimer ?? DEFAULT_DISCLAIMER} compact />;

  function toggle(code: string) {
    setError("");
    setSelected((prev) => (prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]));
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    if (selected.length === 0) return setError("Vui lòng chọn ít nhất một dịch vụ.");
    if (!date) return setError("Vui lòng chọn ngày mong muốn.");
    if (date < todayISO()) return setError("Ngày mong muốn phải từ hôm nay trở đi.");
    if (selected.length > remaining) {
      return setError(
        remaining === 0
          ? "Bạn đang có 3 lịch hẹn chưa hoàn tất. Hãy huỷ bớt hoặc chờ khám xong trước khi đặt thêm."
          : `Bạn chỉ có thể đặt thêm ${remaining} lịch hẹn lúc này.`,
      );
    }
    setSubmitting(true);
    const done: AppointmentOut[] = [];
    try {
      for (const code of selected) {
        done.push(
          await api.createAppointment({
            service_code: code,
            preferred_date: date,
            reason: reason.trim() || undefined,
            consultation_id: consult?.id,
          }),
        );
      }
      setCreated((prev) => [...prev, ...done]);
    } catch (err) {
      if (done.length) {
        // Lịch đã tạo được bỏ khỏi lựa chọn để lần gửi lại không tạo trùng; cập nhật số lịch đang mở
        const doneCodes = new Set(done.map((a) => a.service_code));
        setCreated((prev) => [...prev, ...done]);
        setSelected((prev) => prev.filter((code) => !doneCodes.has(code)));
        setOpenCount((n) => n + done.length);
      }
      setError(errorMessage(err, "Chưa đặt được lịch. Vui lòng thử lại."));
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <SkeletonList rows={4} height="h-20" />;
  if (loadError) return <InlineError message={loadError} onRetry={() => window.location.reload()} />;

  if (created.length > 0 && !error) {
    return (
      <section className="card-padded space-y-4 shadow-sm" aria-live="polite">
        <div className="flex items-start gap-3">
          <CheckCircle2 className="h-6 w-6 shrink-0 text-emerald-600" aria-hidden="true" />
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Đã gửi yêu cầu đặt lịch</h2>
            <p className="text-sm text-slate-600">
              Bệnh viện sẽ xác nhận ngày khám chính thức. Bạn theo dõi trạng thái tại trang tổng quan.
            </p>
          </div>
        </div>
        <ul className="space-y-2">
          {created.map((a) => (
            <li key={a.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 p-3 text-sm">
              <div>
                <p className="font-semibold text-slate-900">{a.service_name}</p>
                <p className="text-xs text-slate-500">Ngày mong muốn: {formatDate(a.preferred_date)}</p>
              </div>
              <div className="flex gap-1.5">
                <PriorityBadge priority={a.priority} />
                <AppointmentStatusBadge status={a.status} />
              </div>
            </li>
          ))}
        </ul>
        {created.some((a) => a.priority === "urgent") && (
          <p className="text-sm text-red-900">
            Lịch của bạn được xếp ưu tiên. Nếu triệu chứng nặng lên trước ngày khám, hãy gọi{" "}
            <a href="tel:115" className="font-bold underline">
              115
            </a>{" "}
            hoặc đến cơ sở y tế gần nhất.
          </p>
        )}
        <div className="flex flex-col gap-2 sm:flex-row">
          <Link href="/patient" className="btn-primary">
            <LayoutDashboard className="h-4 w-4" aria-hidden="true" />
            Về trang tổng quan
          </Link>
          <Link href="/patient/record" className="btn-secondary">
            Xem hồ sơ xuyên suốt
          </Link>
        </div>
        {disclaimer}
      </section>
    );
  }

  return (
    <form onSubmit={submit} className="space-y-6" noValidate>
      {redFlag && (
        <RedFlagAlert
          result={redFlag}
          action={<span className="text-sm font-medium text-red-900">Lịch hẹn của bạn sẽ được xếp ưu tiên.</span>}
        />
      )}
      {!redFlag && urgent && (
        <p className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-900" role="note">
          <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          Lịch khám ưu tiên dành cho người có dấu hiệu cần đánh giá sớm.
        </p>
      )}
      {consult && hint && !redFlag && (
        <p className="flex items-start gap-2 rounded-lg border border-teal-200 bg-teal-50 p-3 text-sm text-teal-900" role="note">
          <Sparkles className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          Dịch vụ phù hợp đã được chọn sẵn theo cuộc trò chuyện với trợ lý. Bạn có thể thay đổi.
        </p>
      )}
      {consultNote && <InlineError message={consultNote} />}

      <fieldset className="card-padded space-y-3">
        <legend className="sr-only">Chọn dịch vụ</legend>
        <div>
          <h2 className="text-base font-semibold text-slate-900">1. Chọn dịch vụ</h2>
          <p className="text-sm text-slate-500">
            Mỗi dịch vụ tạo một lịch hẹn riêng. Bạn có thể đặt thêm {remaining} lịch (tối đa {MAX_OPEN} lịch chưa hoàn tất).
          </p>
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          {services.map((s) => {
            const checked = selected.includes(s.code);
            const suggested = hint?.service_codes.includes(s.code);
            return (
              <label
                key={s.code}
                className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3.5 text-sm transition-colors has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-teal-600 ${
                  checked ? "border-teal-500 bg-teal-50 ring-2 ring-teal-500/20" : "border-slate-200 bg-white hover:border-teal-300"
                }`}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggle(s.code)}
                  className="mt-0.5 h-4 w-4 shrink-0 accent-teal-700"
                />
                <span className="min-w-0 space-y-1">
                  <span className="flex flex-wrap items-center gap-1.5 font-semibold text-slate-900">
                    {s.name}
                    {suggested && (
                      <span className="badge border border-teal-200 bg-white text-teal-800">Được gợi ý</span>
                    )}
                  </span>
                  <span className="block text-xs leading-relaxed text-slate-600">{s.description}</span>
                  {s.cancer_types.length > 0 && !s.cancer_types.includes("other") && (
                    <span className="block text-xs text-slate-500">{s.cancer_types.map(cancerLabel).join(", ")}</span>
                  )}
                </span>
              </label>
            );
          })}
        </div>
      </fieldset>

      <section className="card-padded space-y-4">
        <h2 className="text-base font-semibold text-slate-900">2. Thời gian và lý do</h2>
        <div className="max-w-xs">
          <label htmlFor="book-date" className="label">
            Ngày mong muốn
          </label>
          <input
            id="book-date"
            type="date"
            required
            min={todayISO()}
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="input"
            aria-describedby="book-date-hint"
          />
          <p id="book-date-hint" className="mt-1 text-xs text-slate-500">
            Bệnh viện sẽ xác nhận ngày khám chính thức.
          </p>
        </div>
        <div>
          <label htmlFor="book-reason" className="label">
            Lý do khám (không bắt buộc)
          </label>
          <textarea
            id="book-reason"
            rows={3}
            maxLength={1000}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="input resize-y"
            placeholder="Ví dụ: Muốn được tư vấn tầm soát ung thư vú vì mẹ từng mắc bệnh."
          />
        </div>
      </section>

      {error && <InlineError message={error} />}
      {created.length > 0 && error && (
        <p className="text-sm text-slate-600">
          Đã tạo {created.length} lịch hẹn trước khi gặp lỗi ({created.map((a) => a.service_name).join(", ")}); các dịch
          vụ này đã được bỏ chọn để không đặt trùng.{" "}
          <Link href="/patient" className="font-semibold text-teal-700 underline">
            Xem tại trang tổng quan
          </Link>
          .
        </p>
      )}

      <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
        <Link href="/patient/chat" className="btn-secondary">
          <MessageSquare className="h-4 w-4" aria-hidden="true" />
          Hỏi thêm trợ lý
        </Link>
        <button type="submit" className={urgent ? "btn-danger" : "btn-primary"} disabled={submitting || remaining === 0}>
          {submitting ? (
            <>
              <span className="spinner" aria-hidden="true" />
              Đang xử lý…
            </>
          ) : (
            <>
              <CalendarCheck className="h-4 w-4" aria-hidden="true" />
              {urgent ? "Gửi yêu cầu khám ưu tiên" : "Gửi yêu cầu đặt lịch"}
            </>
          )}
        </button>
      </div>
      {disclaimer}
    </form>
  );
}

export default function BookPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <header>
        <h1 className="page-title flex items-center gap-2">
          <CalendarPlus className="h-6 w-6 text-teal-700" aria-hidden="true" />
          Đặt lịch khám
        </h1>
        <p className="page-subtitle">Đặt lịch mô phỏng: chọn dịch vụ và ngày mong muốn, bệnh viện sẽ xác nhận lại.</p>
      </header>
      <Suspense fallback={<SkeletonList rows={4} height="h-20" />}>
        <BookingForm />
      </Suspense>
    </div>
  );
}
