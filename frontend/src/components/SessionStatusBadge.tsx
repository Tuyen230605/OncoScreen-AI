import type { SessionStatus } from "@/types/api";

const LABEL: Record<SessionStatus, [string, string]> = {
  collecting: ["Đang khảo sát", "bg-slate-200 text-slate-800"],
  red_flag: ["Cần khám sớm", "bg-red-100 text-red-800"],
  pending_review: ["Chờ bác sĩ duyệt", "bg-yellow-100 text-yellow-800"],
  approved: ["Đã duyệt", "bg-green-100 text-green-800"],
  rejected: ["Bác sĩ từ chối", "bg-slate-300 text-slate-800"],
  completed: ["Hoàn thành", "bg-blue-100 text-blue-800"],
};

export function SessionStatusBadge({ status }: { status: SessionStatus }) {
  const [text, cls] = LABEL[status];
  return <span className={`rounded px-2 py-0.5 text-xs font-medium ${cls}`}>{text}</span>;
}
