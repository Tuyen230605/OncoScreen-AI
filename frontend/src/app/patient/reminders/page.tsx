"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ReminderOut } from "@/types/api";

/** TODO(FE): nhóm theo trạng thái, hiển thị message khi due. */
export default function RemindersPage() {
  const [items, setItems] = useState<ReminderOut[]>([]);
  const load = () => api.listReminders().then(setItems).catch(console.error);
  useEffect(() => { load(); }, []);
  return (
    <main className="space-y-3">
      <h1 className="text-lg font-semibold">Lịch nhắc tầm soát</h1>
      <ul className="divide-y rounded bg-white shadow">
        {items.map((r) => (
          <li key={r.id} className="flex items-center justify-between p-3 text-sm">
            <span>{r.cancer_type} · {r.method} · {r.due_date} · <em>{r.status}</em></span>
            {r.status !== "done" && (
              <button className="rounded border px-2 py-1" onClick={() => api.completeReminder(r.id).then(load)}>Đã tầm soát</button>
            )}
          </li>
        ))}
      </ul>
    </main>
  );
}
