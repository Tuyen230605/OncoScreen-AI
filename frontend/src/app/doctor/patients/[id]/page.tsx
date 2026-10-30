"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { errorMessage, isStatus } from "@/lib/errors";
import { formatDateTime } from "@/lib/format";
import { COPILOT_DEFAULT_DISCLAIMER } from "@/lib/labels";
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
import {
  AlertTriangle,
  ArrowLeft,
  Bell,
  CalendarClock,
  ClipboardCheck,
  History,
  MessageSquare,
  UserCircle,
  Users,
} from "@/components/icons";

/** Hồ sơ xuyên suốt đầy đủ (góc nhìn bác sĩ): GET /doctor/patients/{id}/record. */
export default function DoctorPatientRecordPage({ params }: { params: { id: string } }) {
  const [record, setRecord] = useState<PatientRecordOut | null>(null);
  const [error, setError] = useState("");
  const [notFound, setNotFound] = useState(false);

  const load = useCallback(() => {
    setError("");
    api
      .getPatientRecord(params.id)
      .then(setRecord)
      .catch((err) => {
        if (isStatus(err, 404)) setNotFound(true);
        else setError(errorMessage(err, "Chưa tải được hồ sơ bệnh nhân."));
      });
  }, [params.id]);
  useEffect(load, [load]);

  const back = (
    <Link href="/doctor/patients" className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-indigo-700">
      <ArrowLeft className="h-4 w-4" aria-hidden="true" />
      Danh sách bệnh nhân
    </Link>
  );

  if (notFound) {
    return (
      <div className="space-y-4">
        {back}
        <div className="card-padded">
          <EmptyState
            icon={Users}
            title="Không tìm thấy bệnh nhân"
            action={
              <Link href="/doctor/patients" className="btn-doctor">
                Về danh sách
              </Link>
            }
          />
        </div>
      </div>
    );
  }

  const redFlag = record?.timeline.some((e) => e.kind === "red_flag.detected");

  return (
    <div className="space-y-6">
      {back}
      {error && <InlineError message={error} onRetry={load} />}
      {!record && !error && <SkeletonList rows={4} height="h-24" />}
      {record && (
        <>
          <header className="space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="page-title">{record.user.full_name}</h1>
              {redFlag && (
                <span className="badge border border-red-200 bg-red-50 text-red-700">
                  <AlertTriangle className="h-3 w-3" aria-hidden="true" />
                  Có ghi nhận red-flag
                </span>
              )}
            </div>
            <p className="break-all text-sm text-slate-600">
              {record.user.email}, tài khoản tạo {formatDateTime(record.user.created_at)}
            </p>
          </header>

          {/* Hồ sơ có hội thoại Navigator & kết quả Copilot → luôn kèm lưu ý (S6) */}
          <Disclaimer text={record.encounters[0]?.disclaimer ?? COPILOT_DEFAULT_DISCLAIMER} variant="copilot" compact />

          <section className="card-padded">
            <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-slate-900">
              <UserCircle className="h-5 w-5 text-indigo-600" aria-hidden="true" />
              Thông tin sức khoẻ
            </h2>
            <ProfileSummary profile={record.profile} tone="doctor" />
          </section>

          <div className="grid gap-6 lg:grid-cols-5">
            <section className="card-padded lg:col-span-2" aria-labelledby="dr-timeline">
              <h2 id="dr-timeline" className="mb-4 flex items-center gap-2 text-base font-semibold text-slate-900">
                <History className="h-5 w-5 text-indigo-600" aria-hidden="true" />
                Dòng thời gian
              </h2>
              {record.timeline.length ? (
                <RecordTimeline events={record.timeline} showIds />
              ) : (
                <p className="text-sm text-slate-500">Chưa có mốc nào.</p>
              )}
            </section>
            <div className="min-w-0 space-y-6 lg:col-span-3">
              <section className="card-padded">
                <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-slate-900">
                  <ClipboardCheck className="h-5 w-5 text-indigo-600" aria-hidden="true" />
                  Lượt khám
                </h2>
                <EncounterList
                  encounters={record.encounters}
                  appointments={record.appointments}
                  hrefFor={(e) => `/doctor/encounters/${e.id}`}
                />
              </section>
              <section className="card-padded">
                <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-slate-900">
                  <CalendarClock className="h-5 w-5 text-indigo-600" aria-hidden="true" />
                  Lịch hẹn
                </h2>
                <AppointmentList appointments={record.appointments} />
              </section>
              <section className="card-padded">
                <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-slate-900">
                  <Bell className="h-5 w-5 text-indigo-600" aria-hidden="true" />
                  Nhắc lịch
                </h2>
                <ReminderList reminders={record.reminders} />
              </section>
              <section className="card-padded">
                <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-slate-900">
                  <MessageSquare className="h-5 w-5 text-indigo-600" aria-hidden="true" />
                  Tư vấn với Navigator
                </h2>
                <ConsultationList consultations={record.consultations} />
              </section>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
