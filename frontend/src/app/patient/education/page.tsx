"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type EducationTopic } from "@/lib/api";
import { errorMessage } from "@/lib/errors";
import { DEFAULT_DISCLAIMER } from "@/lib/labels";
import type { CancerType, EducationContent } from "@/types/api";
import { Disclaimer } from "@/components/Disclaimer";
import { SimpleMarkdown } from "@/components/SimpleMarkdown";
import { SourceList } from "@/components/SourceList";
import { InlineError, SkeletonText } from "@/components/ui";
import { CheckCircle2, ShieldAlert } from "@/components/icons";

/** Tài liệu giáo dục theo từng loại ung thư (GET /education, /education/{type}). */
export default function EducationPage() {
  const [topics, setTopics] = useState<EducationTopic[]>([]);
  const [active, setActive] = useState<CancerType | null>(null);
  const [selected, setSelected] = useState<EducationContent | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const openTopic = useCallback(async (type: CancerType) => {
    setActive(type);
    setLoading(true);
    setError("");
    try {
      setSelected(await api.getEducation(type));
    } catch (err) {
      setError(errorMessage(err, "Chưa tải được nội dung tài liệu."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    api
      .listEducationTopics()
      .then((data) => {
        setTopics(data);
        if (data.length > 0) void openTopic(data[0].cancer_type);
      })
      .catch((err) => setError(errorMessage(err, "Chưa tải được danh mục tài liệu.")));
  }, [openTopic]);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <header>
        <h1 className="page-title">Tài liệu tầm soát</h1>
        <p className="page-subtitle">Kiến thức về dấu hiệu cảnh báo và cách phòng ngừa, tổng hợp từ hướng dẫn chuyên môn.</p>
      </header>

      <div className="flex flex-wrap gap-2" role="tablist" aria-label="Chủ đề">
        {topics.map((t) => (
          <button
            key={t.cancer_type}
            type="button"
            role="tab"
            aria-selected={active === t.cancer_type}
            onClick={() => void openTopic(t.cancer_type)}
            className={`cursor-pointer rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
              active === t.cancer_type
                ? "bg-teal-700 text-white"
                : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-100"
            }`}
          >
            {t.title}
          </button>
        ))}
      </div>

      {error && <InlineError message={error} onRetry={active ? () => void openTopic(active) : undefined} />}

      {loading ? (
        <div className="card-padded">
          <SkeletonText />
        </div>
      ) : selected ? (
        <article className="card-padded space-y-5">
          <h2 className="text-xl font-bold text-slate-900">{selected.title}</h2>
          {selected.warning_signs.length > 0 && (
            <section className="space-y-2 rounded-lg border border-red-100 border-l-4 border-l-red-400 bg-red-50/50 p-4">
              <h3 className="flex items-center gap-2 text-sm font-semibold text-red-900">
                <ShieldAlert className="h-4 w-4 text-red-600" aria-hidden="true" />
                Dấu hiệu nên đi khám sớm, không chờ lịch tầm soát
              </h3>
              <ul className="grid gap-2 text-sm text-red-950 sm:grid-cols-2">
                {selected.warning_signs.map((sign) => (
                  <li key={sign} className="rounded-md border border-red-100 bg-white p-2">
                    {sign}
                  </li>
                ))}
              </ul>
            </section>
          )}
          <SimpleMarkdown source={selected.body_md} />
          {selected.prevention_tips.length > 0 && (
            <section className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-800">Phòng ngừa chủ động</h3>
              <ul className="grid gap-2 text-sm text-slate-700 sm:grid-cols-2">
                {selected.prevention_tips.map((tip) => (
                  <li key={tip} className="flex items-start gap-2 rounded-md border border-teal-100 bg-teal-50/50 p-2.5">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-teal-700" aria-hidden="true" />
                    <span>{tip}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}
          <SourceList sources={selected.sources} defaultOpen />
        </article>
      ) : null}

      <Disclaimer text={DEFAULT_DISCLAIMER} />
    </div>
  );
}
