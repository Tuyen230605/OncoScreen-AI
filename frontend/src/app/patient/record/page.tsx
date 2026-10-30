"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { errorMessage } from "@/lib/errors";
import { DEFAULT_DISCLAIMER } from "@/lib/labels";
import type { PatientRecordOut } from "@/types/api";
import { Disclaimer } from "@/components/Disclaimer";
import { RecordTimeline } from "@/components/RecordTimeline";
import {
  AppointmentList,
  ConsultationList,
  EncounterList,
  ProfileSummary,
  ReminderList,
} from "@/components/RecordSections";
import { EmptyState, InlineError, SkeletonList } from "@/components/ui";
import { History, UserCircle } from "@/components/icons";

type Tab = "timeline" | "appointments" | "visits" | "consultations";

const TABS: Array<{ id: Tab; label: string }> = [
  { id: "timeline", label: "Dòng thời gian" },
  { id: "appointments", label: "Lịch hẹn" },
  { id: "visits", label: "Lượt khám" },
  { id: "consultations", label: "Tư vấn" },
];

/** Hồ sơ xuyên suốt (góc nhìn bệnh nhân): mọi mốc từ tư vấn, đặt lịch, khám tới nhắc lịch. */
export default function PatientRecordPage() {
  const [record, setRecord] = useState<PatientRecordOut | null>(null);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<Tab>("timeline");

  const load = useCallback(() => {
    setError("");
    api
      .getMyRecord()
      .then(setRecord)
      .catch((err) => setError(errorMessage(err, "Chưa tải được hồ sơ.")));
  }, []);
  useEffect(load, [load]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="page-title">Hồ sơ xuyên suốt</h1>
        <p className="page-subtitle">
          Toàn bộ hành trình của bạn tại bệnh viện: tư vấn với trợ lý, lịch hẹn, kết luận của bác sĩ và nhắc lịch.
        </p>
      </header>

      {error && <InlineError message={error} onRetry={load} />}
      {!record && !error && <SkeletonList rows={4} height="h-16" />}

      {record && (
        <>
          <section className="card-padded">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <h2 className="flex items-center gap-2 text-base font-semibold text-slate-900">
                <UserCircle className="h-5 w-5 text-teal-700" aria-hidden="true" />
                Thông tin sức khoẻ
              </h2>
              <Link href="/patient/profile" className="text-sm font-semibold text-teal-700 underline-offset-2 hover:underline">
                Cập nhật
              </Link>
            </div>
            <ProfileSummary profile={record.profile} />
          </section>

          <div className="flex gap-1 overflow-x-auto rounded-lg border border-slate-200 bg-slate-100 p-1" role="tablist" aria-label="Phần hồ sơ">
            {TABS.map((t) => (
              <button
                key={t.id}
                type="button"
                role="tab"
                id={`tab-${t.id}`}
                aria-selected={tab === t.id}
                aria-controls={`panel-${t.id}`}
                onClick={() => setTab(t.id)}
                className={`shrink-0 cursor-pointer rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  tab === t.id ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          <section id={`panel-${tab}`} role="tabpanel" aria-labelledby={`tab-${tab}`} className="card-padded">
            {tab === "timeline" &&
              (record.timeline.length ? (
                <RecordTimeline events={record.timeline} />
              ) : (
                <EmptyState
                  icon={History}
                  title="Chưa có mốc nào"
                  action={
                    <Link href="/patient/chat" className="btn-primary">
                      Trò chuyện với trợ lý
                    </Link>
                  }
                />
              ))}
            {tab === "appointments" && <AppointmentList appointments={record.appointments} />}
            {tab === "visits" && (
              <div className="space-y-5">
                <EncounterList
                  encounters={record.encounters}
                  appointments={record.appointments}
                  hrefFor={(e) => (e.status === "finalized" ? `/patient/visits/${e.id}` : null)}
                />
                <div>
                  <h3 className="mb-2 text-sm font-semibold text-slate-900">Nhắc lịch từ kế hoạch đã duyệt</h3>
                  <ReminderList reminders={record.reminders} />
                </div>
              </div>
            )}
            {tab === "consultations" && <ConsultationList consultations={record.consultations} />}
          </section>

          {/* Hồ sơ chứa hội thoại & gợi ý của trợ lý → luôn kèm lưu ý y khoa (S6) */}
          <Disclaimer
            text={record.consultations.find((c) => c.last_reply)?.last_reply?.disclaimer ?? DEFAULT_DISCLAIMER}
            compact
          />
        </>
      )}
    </div>
  );
}
