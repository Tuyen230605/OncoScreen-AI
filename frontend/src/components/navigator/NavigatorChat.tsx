"use client";
import { FormEvent, KeyboardEvent, type ReactNode, useCallback, useEffect, useRef, useState } from "react";
import type { Answer, ConsultationOut, NavigatorMessageIn, Questionnaire, ServiceOut, UserOut } from "@/types/api";
import { api } from "@/lib/api";
import { getUser, onSessionExpired } from "@/lib/auth";
import { clearConsult, getStoredConsult, saveConsult, type StoredConsult } from "@/lib/consult";
import { errorMessage, isStatus } from "@/lib/errors";
import { DEFAULT_DISCLAIMER } from "@/lib/labels";
import { initials } from "@/lib/format";
import { Disclaimer } from "@/components/Disclaimer";
import { SourceList } from "@/components/SourceList";
import { InlineError, SkeletonList } from "@/components/ui";
import { QuickCheckForm, valuesFromIntake } from "@/components/navigator/QuickCheckForm";
import { ResultPanel } from "@/components/navigator/ResultPanel";
import { AlertTriangle, Bot, ChevronDown, ListChecks, RefreshCw, Send, User } from "@/components/icons";

const QUICK_PROMPTS = [
  "Tôi 45 tuổi, nữ, mẹ từng bị ung thư vú",
  "Ai nên tầm soát ung thư đại trực tràng?",
  "Tôi nam 58 tuổi, hút thuốc 30 gói-năm",
  "Chụp nhũ ảnh có đau không?",
];

const WELCOME =
  "Xin chào! Mình là trợ lý tầm soát ung thư của bệnh viện. Bạn có thể hỏi về loại ung thư nên tầm soát, độ tuổi bắt đầu và tần suất, hoặc cho mình biết tuổi, giới tính và tiền sử gia đình để nhận gợi ý theo hướng dẫn chuyên môn. Mình không chẩn đoán bệnh; nếu bạn có triệu chứng bất thường, hãy cho mình biết để được hướng dẫn đi khám sớm.";

const MAX_LEN = 2000;

const SESSION_EXPIRED_NOTE =
  "Phiên đăng nhập đã hết hạn. Bạn vẫn có thể hỏi trợ lý ẩn danh, hoặc đăng nhập lại để tiếp tục cuộc trò chuyện của tài khoản.";

/** Khoá lưu phiên tư vấn theo phiên đăng nhập *hiện tại* (đọc lại storage vì phiên có thể vừa hết hạn giữa chừng). */
function currentOwner(): string | null {
  const u = getUser();
  return u?.role === "patient" ? u.id : null;
}

/**
 * Chat với Navigator (dùng chung cho trang công khai "/" và "/patient/chat").
 * - Ẩn danh: phiên lưu `{id, access_token}` ở localStorage, gửi lại qua X-Consult-Token.
 * - Bệnh nhân đã đăng nhập: phiên tạo bằng Bearer (gắn tài khoản), CTA dẫn thẳng tới đặt lịch.
 * - Mã phiên chỉ bị xoá khi backend xác nhận phiên không còn truy cập được (401/404); lỗi mạng/máy chủ thì giữ lại
 *   để thử lại, vì backend chỉ trả `access_token` một lần.
 */
export function NavigatorChat({ mode }: { mode: "public" | "patient" }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [initializing, setInitializing] = useState(true);
  const [consult, setConsult] = useState<ConsultationOut | null>(null);
  const [consultToken, setConsultToken] = useState<string | null>(null);
  /** Phiên đã lưu nhưng chưa tải lại được (lỗi mạng/máy chủ): tin nhắn kế tiếp vẫn gửi vào phiên này. */
  const [unrestored, setUnrestored] = useState<StoredConsult | null>(null);
  const [restoreError, setRestoreError] = useState("");
  const [services, setServices] = useState<ServiceOut[]>([]);
  const [questionnaire, setQuestionnaire] = useState<Questionnaire | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formLoading, setFormLoading] = useState(false);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const resultRef = useRef<HTMLDivElement>(null);

  const patient = user?.role === "patient" ? user : null;
  const storageOwner = patient?.id ?? null;

  const restore = useCallback((stored: StoredConsult, owner: string | null) => {
    setInitializing(true);
    setRestoreError("");
    api
      .getConsultation(stored.id, stored.access_token)
      .then((c) => {
        setConsult(c);
        setConsultToken(stored.access_token);
        setUnrestored(null);
      })
      .catch((err) => {
        if (isStatus(err, 401) || isStatus(err, 404)) {
          // Phiên không còn truy cập được. Nếu do phiên đăng nhập vừa hết hạn thì giữ con trỏ của tài khoản
          // (đăng nhập lại sẽ khôi phục được).
          if (currentOwner() === owner) clearConsult(owner);
          setUnrestored(null);
        } else {
          setUnrestored(stored);
          setRestoreError(errorMessage(err, "Chưa tải lại được cuộc trò chuyện trước đó."));
        }
      })
      .finally(() => setInitializing(false));
  }, []);

  // Khôi phục phiên đang dở (nếu còn hợp lệ)
  useEffect(() => {
    const u = getUser();
    setUser(u);
    const owner = u?.role === "patient" ? u.id : null;
    const stored = getStoredConsult(owner);
    api.listServices().then(setServices).catch(() => setServices([]));
    if (stored) restore(stored, owner);
    else setInitializing(false);
  }, [restore]);

  // JWT hết hạn (API đã xoá phiên): chuyển sang chế độ ẩn danh; cuộc trò chuyện của tài khoản vẫn được giữ
  useEffect(
    () =>
      onSessionExpired(() => {
        setUser(null);
        setConsult(null);
        setConsultToken(null);
        setUnrestored(null);
        setRestoreError("");
        setError(SESSION_EXPIRED_NOTE);
      }),
    [],
  );

  // Cuộn khung chat xuống cuối (chỉ cuộn trong khung, không cuộn cả trang)
  const messageCount = consult?.messages.length ?? 0;
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messageCount, pending, sending, showForm]);

  const ensureConsult = useCallback(async (): Promise<{ id: string; token: string | null }> => {
    if (consult) return { id: consult.id, token: consultToken };
    if (unrestored) return { id: unrestored.id, token: unrestored.access_token };
    const created = await api.createConsultation();
    // Lưu theo phiên đăng nhập sau khi gọi API: nếu JWT vừa hết hạn, phiên mới là phiên ẩn danh
    saveConsult({ id: created.consultation.id, access_token: created.access_token }, currentOwner());
    setConsult(created.consultation);
    setConsultToken(created.access_token);
    return { id: created.consultation.id, token: created.access_token };
  }, [consult, consultToken, unrestored]);

  async function send(body: NavigatorMessageIn, label: string): Promise<boolean> {
    if (sending) return false;
    setSending(true);
    setPending(label);
    setError("");
    try {
      const c = await ensureConsult();
      const updated = await api.sendConsultMessage(c.id, body, c.token);
      setConsult(updated);
      setConsultToken(c.token);
      setUnrestored(null);
      setRestoreError("");
      return true;
    } catch (err) {
      if (isStatus(err, 401) || isStatus(err, 404)) {
        setConsult(null);
        setConsultToken(null);
        setUnrestored(null);
        setRestoreError("");
        if (currentOwner() === storageOwner) {
          clearConsult(storageOwner);
          setError("Phiên tư vấn trước đã hết hiệu lực. Mình đã mở cuộc trò chuyện mới, bạn vui lòng gửi lại.");
        } else {
          // JWT vừa hết hạn: phiên của tài khoản không truy cập được ở chế độ ẩn danh, giữ lại để đăng nhập lại
          setError(SESSION_EXPIRED_NOTE);
        }
      } else {
        setError(errorMessage(err, "Chưa gửi được tin nhắn. Vui lòng thử lại."));
      }
      return false;
    } finally {
      setSending(false);
      setPending(null);
    }
  }

  async function sendMessage(text: string) {
    const value = text.trim();
    if (!value) return;
    if (value.length > MAX_LEN) {
      setError(`Tin nhắn tối đa ${MAX_LEN} ký tự.`);
      return;
    }
    setInput("");
    const ok = await send({ message: value }, value);
    if (!ok) setInput(value);
    inputRef.current?.focus();
  }

  async function sendAnswers(answers: Answer[]) {
    const ok = await send({ answers }, `Đã trả lời bảng hỏi nhanh (${answers.length} câu).`);
    if (ok) {
      setShowForm(false);
      resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  async function openQuickCheck() {
    setShowForm(true);
    if (questionnaire) return;
    setFormLoading(true);
    try {
      setQuestionnaire(await api.getNavigatorQuestionnaire());
    } catch (err) {
      setShowForm(false);
      setError(errorMessage(err, "Chưa tải được bảng hỏi nhanh."));
    } finally {
      setFormLoading(false);
    }
  }

  function resetConversation() {
    clearConsult(storageOwner);
    setConsult(null);
    setConsultToken(null);
    setUnrestored(null);
    setRestoreError("");
    setShowForm(false);
    setError("");
    setInput("");
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void sendMessage(input);
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      void sendMessage(input);
    }
  }

  const messages = consult?.messages ?? [];
  const reply = consult?.last_reply ?? null;
  const lastAssistantIndex = messages.map((m) => m.role).lastIndexOf("assistant");
  const redFlag = Boolean(reply?.red_flag.detected);
  const initial = patient ? initials(patient.full_name) : null;

  return (
    <div className="grid gap-6 lg:grid-cols-5">
      <section
        className="card flex min-w-0 flex-col overflow-hidden lg:sticky lg:top-20 lg:col-span-3 lg:self-start"
        aria-labelledby="navigator-title"
      >
        <header className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 px-4 py-3">
          <div className="flex min-w-0 items-center gap-2.5">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-200 text-slate-600">
              <Bot className="h-4 w-4" aria-hidden="true" />
            </span>
            <div className="min-w-0">
              <h2 id="navigator-title" className="text-sm font-semibold text-slate-900">
                Trợ lý tầm soát (Navigator)
              </h2>
              <p className="text-xs text-slate-500">Trả lời theo hướng dẫn chuyên môn có trích nguồn</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            {!showForm && (
              <button type="button" onClick={() => void openQuickCheck()} className="btn-secondary min-h-[36px] px-3 text-xs">
                <ListChecks className="h-4 w-4" aria-hidden="true" />
                Bảng hỏi nhanh
              </button>
            )}
            {(consult || unrestored) && (
              <button
                type="button"
                onClick={resetConversation}
                disabled={sending}
                className="btn-ghost min-h-[36px] px-2.5 text-xs"
                aria-label="Bắt đầu cuộc trò chuyện mới"
              >
                <RefreshCw className="h-4 w-4" aria-hidden="true" />
                <span className="hidden sm:inline">Trò chuyện mới</span>
              </button>
            )}
          </div>
        </header>

        <div ref={scrollRef} className="h-[28rem] overflow-y-auto px-4 py-4 sm:px-5" aria-live="polite">
          {initializing ? (
            <SkeletonList rows={3} height="h-14" />
          ) : showForm ? (
            formLoading || !questionnaire ? (
              <SkeletonList rows={4} height="h-12" />
            ) : (
              <QuickCheckForm
                questionnaire={questionnaire}
                initial={valuesFromIntake(consult?.intake)}
                submitting={sending}
                onSubmit={(answers) => void sendAnswers(answers)}
                onCancel={() => setShowForm(false)}
              />
            )
          ) : (
            <ol className="space-y-4">
              <AssistantBubble content={WELCOME} />
              {messages.map((m, i) =>
                m.role === "user" ? (
                  <UserBubble key={i} content={m.content} initial={initial} />
                ) : (
                  <AssistantBubble key={i} content={m.content}>
                    {i === lastAssistantIndex && reply && (
                      <>
                        {reply.insufficient_evidence && (
                          <p className="flex items-start gap-1.5 rounded-md border border-amber-200 bg-amber-50 p-2 text-xs text-amber-800">
                            <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                            Chưa đủ tài liệu hướng dẫn để trả lời có căn cứ; bạn nên hỏi trực tiếp bác sĩ.
                          </p>
                        )}
                        <SourceList sources={reply.sources} />
                      </>
                    )}
                  </AssistantBubble>
                ),
              )}
              {pending && <UserBubble content={pending} initial={initial} />}
              {sending && <TypingBubble />}
            </ol>
          )}
        </div>

        {redFlag && !showForm && (
          <button
            type="button"
            onClick={() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })}
            className="mx-4 mb-2 flex cursor-pointer items-center justify-between gap-2 rounded-lg border border-red-200 border-l-4 border-l-red-500 bg-red-50 px-3 py-2 text-left text-sm font-medium text-red-900 lg:hidden"
          >
            <span className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0 text-red-600" aria-hidden="true" />
              Có dấu hiệu cần khám sớm, xem hướng dẫn
            </span>
            <ChevronDown className="h-4 w-4 shrink-0" aria-hidden="true" />
          </button>
        )}

        {!showForm && (
          <div className="border-t border-slate-200 bg-white px-4 py-3">
            {messages.length === 0 && !initializing && (
              <div className="mb-3 flex flex-wrap gap-2" aria-label="Gợi ý câu hỏi">
                {QUICK_PROMPTS.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => void sendMessage(p)}
                    disabled={sending}
                    className="cursor-pointer rounded-full border border-slate-200 px-3 py-1.5 text-left text-sm text-slate-700 transition-colors hover:border-teal-300 hover:bg-teal-50 disabled:opacity-50"
                  >
                    {p}
                  </button>
                ))}
              </div>
            )}
            {restoreError && unrestored && (
              <div className="mb-3">
                <InlineError message={restoreError} onRetry={() => restore(unrestored, storageOwner)} />
              </div>
            )}
            {error && (
              <div className="mb-3">
                <InlineError message={error} />
              </div>
            )}
            <form onSubmit={onSubmit} className="flex items-end gap-2">
              <label htmlFor={`navigator-input-${mode}`} className="sr-only">
                Nhập câu hỏi cho trợ lý
              </label>
              <textarea
                id={`navigator-input-${mode}`}
                ref={inputRef}
                rows={1}
                maxLength={MAX_LEN}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                disabled={sending || initializing}
                placeholder="Ví dụ: Tôi 50 tuổi, nam, có cần tầm soát gì không?"
                className="input max-h-40 min-h-[44px] flex-1 resize-y rounded-xl"
              />
              <button
                type="submit"
                disabled={sending || initializing || !input.trim()}
                className="btn-primary h-11 shrink-0 rounded-xl px-4"
                aria-label="Gửi tin nhắn"
              >
                {sending ? <span className="spinner" aria-hidden="true" /> : <Send className="h-4 w-4" aria-hidden="true" />}
                <span className="hidden sm:inline">Gửi</span>
              </button>
            </form>
            <p className="mt-2 text-xs text-slate-500">
              Enter để gửi, Shift + Enter để xuống dòng. Không nhập số CCCD, số điện thoại hay thông tin định danh.
            </p>
          </div>
        )}
      </section>

      <aside ref={resultRef} id="navigator-result" className="min-w-0 scroll-mt-24 space-y-4 lg:col-span-2" aria-label="Kết quả tham khảo">
        <ResultPanel
          reply={reply}
          intake={consult?.intake ?? null}
          consultId={consult?.id ?? null}
          isPatient={Boolean(patient)}
          services={services}
          onOpenQuickCheck={() => void openQuickCheck()}
        />
        <Disclaimer text={reply?.disclaimer ?? DEFAULT_DISCLAIMER} />
      </aside>
    </div>
  );
}

function AssistantBubble({ content, children }: { content: string; children?: ReactNode }) {
  return (
    <li className="flex items-start gap-2.5">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-200 text-slate-600">
        <Bot className="h-4 w-4" aria-hidden="true" />
        <span className="sr-only">Trợ lý:</span>
      </span>
      <div className="min-w-0 max-w-[85%] space-y-2">
        <div className="whitespace-pre-wrap break-words rounded-2xl rounded-bl-md bg-slate-100 px-4 py-2.5 text-sm leading-relaxed text-slate-800">
          {content}
        </div>
        {children}
      </div>
    </li>
  );
}

function UserBubble({ content, initial }: { content: string; initial: string | null }) {
  return (
    <li className="flex items-start justify-end gap-2.5">
      <div className="min-w-0 max-w-[80%] whitespace-pre-wrap break-words rounded-2xl rounded-br-md bg-teal-700 px-4 py-2.5 text-sm leading-relaxed text-white">
        <span className="sr-only">Bạn: </span>
        {content}
      </div>
      <span
        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-teal-100 text-xs font-semibold text-teal-700"
        aria-hidden="true"
      >
        {initial ?? <User className="h-4 w-4" aria-hidden="true" />}
      </span>
    </li>
  );
}

function TypingBubble() {
  return (
    <li className="flex items-start gap-2.5" aria-label="Trợ lý đang soạn trả lời">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-200 text-slate-600">
        <Bot className="h-4 w-4" aria-hidden="true" />
      </span>
      <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-md bg-slate-100 px-4 py-3">
        <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:0.15s]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:0.3s]" />
      </div>
    </li>
  );
}
