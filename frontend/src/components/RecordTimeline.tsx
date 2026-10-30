"use client";
import type { RecordEventOut } from "@/types/api";
import { eventKindLabel } from "@/lib/labels";
import { formatDateTime } from "@/lib/format";
import {
  AlertTriangle,
  Bell,
  CalendarCheck,
  CalendarPlus,
  CheckCircle2,
  ClipboardCheck,
  History,
  MessageSquare,
  Stethoscope,
  UserCircle,
  UserPlus,
  XCircle,
  type IconType,
} from "@/components/icons";

function iconFor(kind: string): { icon: IconType; tone: string } {
  if (kind === "red_flag.detected") return { icon: AlertTriangle, tone: "bg-red-100 text-red-700" };
  if (kind === "account.created") return { icon: UserPlus, tone: "bg-slate-100 text-slate-600" };
  if (kind === "consult.summary") return { icon: MessageSquare, tone: "bg-teal-50 text-teal-700" };
  if (kind === "appointment.requested") return { icon: CalendarPlus, tone: "bg-amber-50 text-amber-700" };
  if (kind === "appointment.confirmed") return { icon: CalendarCheck, tone: "bg-sky-50 text-sky-700" };
  if (kind === "appointment.cancelled") return { icon: XCircle, tone: "bg-slate-100 text-slate-500" };
  if (kind === "appointment.escalated") return { icon: AlertTriangle, tone: "bg-red-100 text-red-700" };
  if (kind === "encounter.started") return { icon: Stethoscope, tone: "bg-indigo-50 text-indigo-700" };
  if (kind === "encounter.finalized") return { icon: ClipboardCheck, tone: "bg-emerald-50 text-emerald-700" };
  if (kind === "reminder.done") return { icon: CheckCircle2, tone: "bg-emerald-50 text-emerald-700" };
  if (kind.startsWith("reminder.")) return { icon: Bell, tone: "bg-amber-50 text-amber-700" };
  if (kind === "profile.updated") return { icon: UserCircle, tone: "bg-slate-100 text-slate-600" };
  return { icon: History, tone: "bg-slate-100 text-slate-600" };
}

export const timelineAnchor = (id: string) => `record-event-${id}`;

/** Dòng thời gian hồ sơ xuyên suốt (mới nhất trước). `highlightIds`: mốc được dẫn chứng bởi brief/Copilot. */
export function RecordTimeline({
  events,
  highlightIds = [],
  showIds = false,
}: {
  events: RecordEventOut[];
  highlightIds?: string[];
  showIds?: boolean;
}) {
  const highlighted = new Set(highlightIds);
  return (
    <ol className="relative space-y-3 border-l border-slate-200 pl-5" aria-label="Dòng thời gian hồ sơ">
      {events.map((e) => {
        const { icon: Icon, tone } = iconFor(e.kind);
        const active = highlighted.has(e.id);
        return (
          <li
            key={e.id}
            id={timelineAnchor(e.id)}
            className={`relative scroll-mt-24 rounded-lg p-2.5 transition-colors ${
              active ? "bg-indigo-50 ring-2 ring-indigo-400" : ""
            }`}
            aria-current={active ? "true" : undefined}
          >
            <span
              className={`absolute -left-[33px] top-2.5 flex h-6 w-6 items-center justify-center rounded-full ring-4 ring-white ${tone}`}
              aria-hidden="true"
            >
              <Icon className="h-3.5 w-3.5" aria-hidden />
            </span>
            <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
              <span className="text-sm font-semibold text-slate-900">{eventKindLabel(e.kind)}</span>
              <span className="text-xs text-slate-500">{formatDateTime(e.at)}</span>
            </div>
            <p className="mt-0.5 text-sm leading-relaxed text-slate-700">{e.summary}</p>
            {showIds && <p className="mt-1 break-all text-[11px] text-slate-400">Mã mốc: {e.id}</p>}
          </li>
        );
      })}
    </ol>
  );
}
