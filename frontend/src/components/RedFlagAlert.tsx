import type { RedFlagResult } from "@/types/api";

/** Cảnh báo dấu hiệu cần khám sớm — giọng điệu bình tĩnh, KHÔNG hiển thị plan (S3). */
export function RedFlagAlert({ result }: { result: RedFlagResult }) {
  return (
    <section role="alert" className="rounded-lg border-2 border-red-400 bg-red-50 p-4">
      <h2 className="text-lg font-semibold text-red-800">Bạn nên đi khám sớm</h2>
      {result.message && <p className="mt-1 text-sm text-red-900">{result.message}</p>}
      <ul className="mt-3 space-y-2">
        {result.flags.map((f) => (
          <li key={f.code} className="rounded bg-white p-2 text-sm">
            <span className={`mr-2 rounded px-2 py-0.5 text-xs text-white ${f.severity === "urgent" ? "bg-red-600" : "bg-orange-500"}`}>
              {f.severity === "urgent" ? "Khám ngay" : "Khám sớm"}
            </span>
            <strong>{f.symptom}</strong> — {f.advice}
          </li>
        ))}
      </ul>
      <button className="mt-4 rounded bg-red-600 px-4 py-2 text-white">Tìm cơ sở y tế gần nhất (mô phỏng)</button>
    </section>
  );
}
