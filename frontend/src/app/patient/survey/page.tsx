"use client";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Answer, Question, SessionOut } from "@/types/api";

/**
 * Khảo sát động: render questionnaire, ẩn/hiện theo depends_on, submit → chuyển trang kết quả.
 * TODO(FE): tách QuestionForm component, validate required, UI từng bước (wizard).
 */
function Survey() {
  const params = useSearchParams();
  const router = useRouter();
  const sessionId = params.get("session");
  const [session, setSession] = useState<SessionOut | null>(null);
  const [answers, setAnswers] = useState<Record<string, unknown>>({});

  useEffect(() => {
    if (sessionId) api.getSession(sessionId).then(setSession).catch(console.error);
  }, [sessionId]);

  const visible = (q: Question) => {
    if (!q.depends_on) return true;
    const [k, v] = q.depends_on.split("=");
    return String(answers[k] ?? "").toLowerCase() === v.toLowerCase();
  };

  async function submit() {
    if (!sessionId) return;
    const payload: Answer[] = Object.entries(answers).map(([question_id, value]) => ({ question_id, value }));
    const res = await api.submitAnswers(sessionId, { answers: payload });
    router.push(`/patient/results/${res.id}`);
  }

  if (!session?.questionnaire) return <p>Đang tải bộ câu hỏi…</p>;
  return (
    <main className="space-y-4">
      <h1 className="text-lg font-semibold">Khảo sát đánh giá nguy cơ</h1>
      {session.questionnaire.questions.filter(visible).map((q) => (
        <div key={q.id} className="rounded bg-white p-3 shadow">
          <label className="block text-sm font-medium">{q.text}{q.required && " *"}</label>
          {q.type === "boolean" && (
            <div className="mt-1 flex gap-3 text-sm">
              <label><input type="radio" name={q.id} onChange={() => setAnswers({ ...answers, [q.id]: true })} /> Có</label>
              <label><input type="radio" name={q.id} onChange={() => setAnswers({ ...answers, [q.id]: false })} /> Không</label>
            </div>
          )}
          {q.type === "number" && <input type="number" className="mt-1 rounded border p-1" onChange={(e) => setAnswers({ ...answers, [q.id]: Number(e.target.value) })} />}
          {q.type === "text" && <input className="mt-1 w-full rounded border p-1" onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })} />}
          {q.type === "single_choice" && (
            <select className="mt-1 rounded border p-1" onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })} defaultValue="">
              <option value="" disabled>Chọn…</option>
              {q.options?.map((o) => <option key={o}>{o}</option>)}
            </select>
          )}
          {q.type === "multi_choice" && (
            <div className="mt-1 flex flex-wrap gap-3 text-sm">
              {q.options?.map((o) => (
                <label key={o}>
                  <input type="checkbox" onChange={(e) => {
                    const cur = new Set((answers[q.id] as string[] | undefined) ?? []);
                    e.target.checked ? cur.add(o) : cur.delete(o);
                    setAnswers({ ...answers, [q.id]: [...cur] });
                  }} /> {o}
                </label>
              ))}
            </div>
          )}
        </div>
      ))}
      <button onClick={submit} className="rounded bg-blue-600 px-4 py-2 text-white">Gửi câu trả lời</button>
    </main>
  );
}

export default function SurveyPage() {
  return <Suspense><Survey /></Suspense>;
}
