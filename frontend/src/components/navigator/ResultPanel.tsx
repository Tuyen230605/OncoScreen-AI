"use client";
import Link from "next/link";
import type { ReactNode } from "react";
import type { IntakeProfile, NavigatorReply, ServiceOut } from "@/types/api";
import { cancerLabel, GENDER_LABEL, MISSING_INFO_LABEL, SYMPTOM_LABEL } from "@/lib/labels";
import { RedFlagAlert } from "@/components/RedFlagAlert";
import { RiskFactorList, SuggestionCard } from "@/components/navigator/SuggestionCard";
import { CalendarPlus, HelpCircle, ListChecks, LogIn, Sparkles, UserPlus } from "@/components/icons";

function Chip({ children, tone = "default" }: { children: ReactNode; tone?: "default" | "warn" }) {
  return (
    <li
      className={`badge border py-1 ${
        tone === "warn" ? "border-amber-200 bg-amber-50 text-amber-900" : "border-slate-200 bg-white text-slate-700"
      }`}
    >
      {children}
    </li>
  );
}

/** "Trợ lý đã hiểu": các thông tin rút ra từ cuộc trò chuyện / bảng hỏi. */
export function IntakeChips({ intake }: { intake: IntakeProfile }) {
  const chips: Array<{ key: string; node: ReactNode; tone?: "warn" }> = [];
  if (intake.age !== null) chips.push({ key: "age", node: `${intake.age} tuổi` });
  if (intake.gender) chips.push({ key: "gender", node: `Giới tính: ${GENDER_LABEL[intake.gender]}` });
  if (intake.family_history.length) {
    chips.push({
      key: "family",
      node: `Người thân mắc: ${intake.family_history.map((t) => cancerLabel(t).replace("Ung thư ", "")).join(", ")}`,
    });
  }
  if (intake.personal_cancer_history !== null) {
    chips.push({ key: "pch", node: intake.personal_cancer_history ? "Có tiền sử ung thư" : "Không có tiền sử ung thư" });
  }
  if (intake.smoking !== null) {
    chips.push({
      key: "smoking",
      node: intake.smoking
        ? intake.pack_years !== null
          ? `Hút thuốc: ${intake.pack_years} gói-năm`
          : "Có hút thuốc"
        : "Không hút thuốc",
    });
  }
  if (intake.hepatitis_b_or_c !== null) {
    chips.push({ key: "hep", node: intake.hepatitis_b_or_c ? "Viêm gan B/C mạn" : "Không viêm gan B/C" });
  }
  if (intake.cirrhosis) chips.push({ key: "cir", node: "Xơ gan" });
  if (intake.hpv_vaccinated !== null) {
    chips.push({ key: "hpv", node: intake.hpv_vaccinated ? "Đã tiêm vắc-xin HPV" : "Chưa tiêm vắc-xin HPV" });
  }
  intake.symptom_codes.forEach((code) =>
    chips.push({ key: code, node: SYMPTOM_LABEL[code] ?? code, tone: "warn" }),
  );

  if (!chips.length) {
    return <p className="text-sm text-slate-500">Trợ lý chưa có thông tin nào về bạn. Hãy kể ngắn gọn hoặc làm bảng hỏi nhanh.</p>;
  }
  return (
    <ul className="flex flex-wrap gap-1.5" aria-label="Thông tin trợ lý đã ghi nhận">
      {chips.map((c) => (
        <Chip key={c.key} tone={c.tone}>
          {c.node}
        </Chip>
      ))}
    </ul>
  );
}

/** CTA đặt lịch theo `next_action` + `booking_hint`. */
export function BookingCta({
  reply,
  consultId,
  isPatient,
  services,
}: {
  reply: NavigatorReply;
  consultId: string;
  isPatient: boolean;
  services: ServiceOut[];
}) {
  const hint = reply.booking_hint;
  if (!hint || reply.next_action === "continue_chat") return null;
  const urgent = reply.next_action === "urgent_care" || hint.priority === "urgent";
  const names = hint.service_codes.map((c) => services.find((s) => s.code === c)?.name ?? c);
  const bookHref = `/patient/book?consult=${encodeURIComponent(consultId)}`;
  const registerHref = `/register?consult=${encodeURIComponent(consultId)}`;
  const loginHref = `/login?consult=${encodeURIComponent(consultId)}`;
  const primaryClass = urgent ? "btn-danger" : "btn-primary";

  return (
    <section
      className={`space-y-3 rounded-xl border p-4 ${
        urgent ? "border-red-200 bg-white" : "border-teal-200 bg-teal-50/60 shadow-sm"
      }`}
      aria-labelledby="booking-cta-title"
    >
      <h2 id="booking-cta-title" className="flex items-center gap-2 text-base font-semibold text-slate-900">
        <CalendarPlus className={`h-5 w-5 ${urgent ? "text-red-600" : "text-teal-700"}`} aria-hidden="true" />
        {urgent ? "Đặt lịch khám ưu tiên" : "Đặt lịch để bác sĩ tư vấn kế hoạch riêng"}
      </h2>
      <p className="text-sm leading-relaxed text-slate-700">{hint.reason}</p>
      {names.length > 0 && (
        <ul className="flex flex-wrap gap-1.5" aria-label="Dịch vụ gợi ý">
          {names.map((n) => (
            <li key={n} className="badge border border-slate-200 bg-white text-slate-700">
              {n}
            </li>
          ))}
        </ul>
      )}
      {isPatient ? (
        <Link href={bookHref} className={`${primaryClass} w-full sm:w-auto`}>
          <CalendarPlus className="h-4 w-4" aria-hidden="true" />
          {urgent ? "Đặt lịch ưu tiên ngay" : "Đặt lịch khám"}
        </Link>
      ) : (
        <div className="flex flex-col gap-2 sm:flex-row">
          <Link href={registerHref} className={`${primaryClass} w-full sm:w-auto`}>
            <UserPlus className="h-4 w-4" aria-hidden="true" />
            Tạo tài khoản để đặt lịch
          </Link>
          <Link href={loginHref} className="btn-secondary w-full sm:w-auto">
            <LogIn className="h-4 w-4" aria-hidden="true" />
            Đã có tài khoản
          </Link>
        </div>
      )}
      {!isPatient && (
        <p className="text-xs text-slate-500">
          Thông tin bạn đã chia sẻ sẽ được gắn vào hồ sơ để bác sĩ xem trước buổi khám, bạn không phải khai lại.
        </p>
      )}
    </section>
  );
}

/** Bảng kết quả tham khảo của lượt Navigator mới nhất. */
export function ResultPanel({
  reply,
  intake,
  consultId,
  isPatient,
  services,
  onOpenQuickCheck,
}: {
  reply: NavigatorReply | null;
  intake: IntakeProfile | null;
  consultId: string | null;
  isPatient: boolean;
  services: ServiceOut[];
  onOpenQuickCheck: () => void;
}) {
  const redFlag = reply?.red_flag.detected ? reply.red_flag : null;
  return (
    <div className="space-y-4">
      {redFlag && reply && consultId && (
        <RedFlagAlert
          result={redFlag}
          action={
            isPatient ? (
              <Link href={`/patient/book?consult=${encodeURIComponent(consultId)}`} className="btn-danger w-full sm:w-auto">
                <CalendarPlus className="h-4 w-4" aria-hidden="true" />
                Đặt lịch ưu tiên
              </Link>
            ) : (
              <div className="flex flex-col gap-2 sm:flex-row">
                <Link href={`/register?consult=${encodeURIComponent(consultId)}`} className="btn-danger w-full sm:w-auto">
                  <CalendarPlus className="h-4 w-4" aria-hidden="true" />
                  Tạo tài khoản, đặt lịch ưu tiên
                </Link>
                <Link href={`/login?consult=${encodeURIComponent(consultId)}`} className="btn-secondary w-full sm:w-auto">
                  <LogIn className="h-4 w-4" aria-hidden="true" />
                  Đã có tài khoản
                </Link>
              </div>
            )
          }
        />
      )}

      <section className="card p-4" aria-labelledby="intake-title">
        <h2 id="intake-title" className="mb-2.5 flex items-center gap-2 text-sm font-semibold text-slate-900">
          <Sparkles className="h-4 w-4 text-teal-700" aria-hidden="true" />
          Trợ lý đã hiểu về bạn
        </h2>
        {intake ? <IntakeChips intake={intake} /> : <IntakeChips intake={EMPTY} />}
        {reply && reply.missing_info.length > 0 && !redFlag && (
          <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="flex items-center gap-1.5 text-sm font-medium text-slate-800">
              <HelpCircle className="h-4 w-4 text-slate-500" aria-hidden="true" />
              Để gợi ý chính xác hơn, trợ lý cần thêm:
            </p>
            <ul className="mt-1.5 list-disc space-y-0.5 pl-6 text-sm text-slate-600">
              {reply.missing_info.map((m) => (
                <li key={m}>{MISSING_INFO_LABEL[m] ?? m}</li>
              ))}
            </ul>
            <button type="button" onClick={onOpenQuickCheck} className="btn-secondary mt-2.5 text-xs">
              <ListChecks className="h-4 w-4" aria-hidden="true" />
              Trả lời bảng hỏi nhanh
            </button>
          </div>
        )}
      </section>

      {reply && !redFlag && reply.suggestions.length > 0 && (
        <section aria-labelledby="suggestions-title" className="space-y-2.5">
          <div>
            <h2 id="suggestions-title" className="text-base font-semibold text-slate-900">
              Gợi ý tầm soát theo hướng dẫn
            </h2>
            <p className="text-xs text-slate-500">Tham khảo theo guideline; bác sĩ sẽ cùng bạn quyết định kế hoạch cụ thể.</p>
          </div>
          {reply.suggestions.map((s) => (
            <SuggestionCard key={s.rule_id} suggestion={s} />
          ))}
        </section>
      )}

      {reply && !redFlag && reply.risk_factors.length > 0 && (
        <section aria-labelledby="risk-title" className="space-y-2.5">
          <h2 id="risk-title" className="text-base font-semibold text-slate-900">
            Yếu tố cần lưu ý
          </h2>
          <RiskFactorList factors={reply.risk_factors} />
        </section>
      )}

      {reply && !redFlag && consultId && (
        <BookingCta reply={reply} consultId={consultId} isPatient={isPatient} services={services} />
      )}
    </div>
  );
}

const EMPTY: IntakeProfile = {
  age: null,
  gender: null,
  family_history: [],
  personal_cancer_history: null,
  smoking: null,
  pack_years: null,
  hepatitis_b_or_c: null,
  cirrhosis: null,
  hpv_vaccinated: null,
  symptom_codes: [],
};
