"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { SessionOut } from "@/types/api";
import { Disclaimer } from "@/components/Disclaimer";
import { RedFlagAlert } from "@/components/RedFlagAlert";
import { PlanTable } from "@/components/PlanTable";
import { SessionStatusBadge } from "@/components/SessionStatusBadge";

/**
 * Màn kết quả — rẽ nhánh theo status:
 *  - collecting   → link tiếp tục khảo sát
 *  - red_flag     → RedFlagAlert, không hiển thị plan
 *  - pending_review → thông báo chờ + polling 10s
 *  - rejected     → thông báo bác sĩ chưa duyệt + ghi chú
 *  - approved     → risk assessment + PlanTable (final_plan)
 */
export default function ResultPage({ params }: { params: { id: string } }) {
  const [s, setS] = useState<SessionOut | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    function load() {
      api.getSession(params.id).then(setS).catch(console.error);
    }
    load();

    // Poll mỗi 10s khi đang pending_review
    timerRef.current = setInterval(() => {
      setS((prev) => {
        if (prev?.status === "pending_review" || prev === null) {
          load();
        }
        return prev;
      });
    }, 10_000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  // Dừng polling khi session không còn pending
  useEffect(() => {
    if (s && s.status !== "pending_review" && timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, [s?.status, s]);

  if (!s) {
    return (
      <div className="flex min-h-[300px] items-center justify-center">
        <span className="spinner h-6 w-6 text-blue-500" aria-label="Đang tải…" />
      </div>
    );
  }

  return (
    <div className="fade-in mx-auto max-w-3xl space-y-6">
      {/* ===== Header ===== */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex-1">
          <h1 className="page-title">Kết quả đánh giá</h1>
          <p className="page-subtitle">
            {new Date(s.created_at).toLocaleDateString("vi-VN", {
              weekday: "long",
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {s.has_red_flag && <span className="badge bg-red-100 text-red-700">⚠ KHẨN</span>}
          <SessionStatusBadge status={s.status} />
        </div>
      </div>

      {/* ===== Collecting: chưa hoàn thành ===== */}
      {s.status === "collecting" && (
        <div className="card-padded space-y-3 text-center">
          <p className="text-4xl">📋</p>
          <p className="text-sm text-slate-700">Phiên khảo sát của bạn vẫn đang trong quá trình thu thập câu trả lời.</p>
          <Link
            href={`/patient/survey?session=${s.id}`}
            className="btn-primary inline-flex"
          >
            Tiếp tục khảo sát →
          </Link>
        </div>
      )}

      {/* ===== Red flag: dừng tư vấn, cảnh báo khám sớm ===== */}
      {s.status === "red_flag" && s.red_flag && (
        <RedFlagAlert result={s.red_flag} />
      )}

      {/* ===== Pending review: chờ bác sĩ ===== */}
      {s.status === "pending_review" && (
        <div className="card-padded flex flex-col items-center gap-3 py-8 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-yellow-100">
            <span className="text-2xl">⏳</span>
          </div>
          <div>
            <p className="font-semibold text-slate-800">Đang chờ bác sĩ xem xét</p>
            <p className="mt-1 text-sm text-slate-600">
              Bác sĩ sẽ xem xét và phê duyệt kết quả khuyến nghị trước khi bạn được xem.
              <br />
              Trang này tự động cập nhật mỗi 10 giây.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="spinner h-3 w-3 text-yellow-500" />
            Đang chờ phê duyệt…
          </div>
        </div>
      )}

      {/* ===== Rejected: bác sĩ chưa duyệt ===== */}
      {s.status === "rejected" && (
        <div className="card-padded space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🚫</span>
            <p className="font-semibold text-slate-800">Bác sĩ chưa phê duyệt kế hoạch này</p>
          </div>
          {s.doctor_note && (
            <blockquote className="rounded-lg border-l-4 border-slate-300 bg-slate-50 p-3 text-sm italic text-slate-700">
              &ldquo;{s.doctor_note}&rdquo;
              {s.reviewed_by && (
                <footer className="mt-1 text-xs not-italic text-slate-500">
                  — {s.reviewed_by.full_name}
                  {s.reviewed_at && `, ${new Date(s.reviewed_at).toLocaleDateString("vi-VN")}`}
                </footer>
              )}
            </blockquote>
          )}
          <p className="text-sm text-slate-600">
            Bạn có thể bắt đầu một phiên đánh giá mới hoặc liên hệ trực tiếp với cơ sở y tế.
          </p>
          <Link href="/patient" className="btn-secondary inline-flex">
            ← Quay về tổng quan
          </Link>
        </div>
      )}

      {/* ===== Approved: hiển thị kết quả đầy đủ ===== */}
      {s.status === "approved" && s.final_plan && (
        <div className="space-y-5">
          {/* Risk assessment */}
          {s.risk_assessment && (
            <section className="card-padded space-y-3">
              <h2 className="font-semibold text-slate-800">📊 Đánh giá nguy cơ</h2>
              <p className="text-sm text-slate-700">{s.risk_assessment.overall_summary}</p>
              {s.risk_assessment.factors.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {s.risk_assessment.factors.map((f) => (
                    <div
                      key={f.cancer_type}
                      className={`rounded-lg border px-3 py-2 text-xs ${
                        f.level === "high"
                          ? "border-red-200 bg-red-50 text-red-700"
                          : f.level === "elevated"
                          ? "border-yellow-200 bg-yellow-50 text-yellow-700"
                          : "border-green-200 bg-green-50 text-green-700"
                      }`}
                    >
                      <span className="font-semibold uppercase">{f.cancer_type}</span>
                      {" · "}
                      {f.level === "high" ? "Nguy cơ cao" : f.level === "elevated" ? "Nguy cơ tăng" : "Nguy cơ trung bình"}
                      {f.reasons.length > 0 && (
                        <ul className="mt-1 list-disc pl-3 text-[11px] opacity-80">
                          {f.reasons.map((r) => <li key={r}>{r}</li>)}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {/* Final plan */}
          <section className="card-padded space-y-3">
            <h2 className="font-semibold text-slate-800">📋 Kế hoạch tầm soát được phê duyệt</h2>
            <PlanTable plan={s.final_plan} />
          </section>

          {/* Reviewed by */}
          {s.reviewed_by && (
            <p className="text-xs text-slate-500 text-right">
              ✓ Đã duyệt bởi <strong>{s.reviewed_by.full_name}</strong>
              {s.reviewed_at && ` · ${new Date(s.reviewed_at).toLocaleString("vi-VN")}`}
            </p>
          )}

          {/* Reminders CTA */}
          {s.reminders && s.reminders.length > 0 && (
            <section className="card-padded bg-blue-50 border-blue-100 space-y-2">
              <p className="text-sm font-medium text-blue-800">🔔 Lịch nhắc đã được tạo</p>
              <p className="text-xs text-blue-700">
                Hệ thống đã tạo {s.reminders.length} lịch nhắc tầm soát. Xem chi tiết trong trang Nhắc lịch.
              </p>
              <Link href="/patient/reminders" className="btn-primary inline-flex text-sm">
                Xem lịch nhắc →
              </Link>
            </section>
          )}
        </div>
      )}

      {/* ===== Disclaimer bắt buộc ở mọi màn kết quả ===== */}
      <Disclaimer text={s.disclaimer} />

      {/* ===== Back link ===== */}
      <div>
        <Link href="/patient" className="text-sm text-slate-500 hover:text-slate-800 hover:underline">
          ← Quay về tổng quan
        </Link>
      </div>
    </div>
  );
}
