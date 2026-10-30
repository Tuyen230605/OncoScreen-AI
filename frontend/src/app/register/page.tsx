"use client";
import Link from "next/link";
import { FormEvent, Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { getUser, homeFor, saveSession } from "@/lib/auth";
import { anonymousConsultToken, clearConsult, getStoredConsult, saveConsult } from "@/lib/consult";
import { errorMessage } from "@/lib/errors";
import { Brand } from "@/components/Brand";
import { InlineError } from "@/components/ui";
import { CheckCircle2, Info, MessageSquare, UserPlus } from "@/components/icons";

function RegisterForm() {
  const router = useRouter();
  const params = useSearchParams();
  const consultParam = params.get("consult");

  const [consult, setConsult] = useState<{ id: string; token: string } | null>(null);
  const [consultMissing, setConsultMissing] = useState(false);
  const [attach, setAttach] = useState(true);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    const u = getUser();
    if (u) {
      router.replace(
        u.role === "patient" && consultParam ? `/patient/book?consult=${encodeURIComponent(consultParam)}` : homeFor(u.role),
      );
      return;
    }
    // Phiên được chỉ định qua ?consult=, nếu không thì phiên ẩn danh đang lưu (nếu có)
    const id = consultParam ?? getStoredConsult(null)?.id ?? null;
    if (!id) return;
    const token = anonymousConsultToken(id);
    if (token) setConsult({ id, token });
    else if (consultParam) setConsultMissing(true);
  }, [consultParam, router]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 6) {
      setError("Mật khẩu tối thiểu 6 ký tự.");
      return;
    }
    if (password !== confirm) {
      setError("Mật khẩu nhập lại chưa khớp.");
      return;
    }
    const linked = attach && consult ? consult : null;
    setLoading(true);
    try {
      await api.register({
        email: email.trim(),
        password,
        full_name: fullName.trim(),
        role: "patient",
        ...(linked ? { consultation_id: linked.id, consultation_token: linked.token } : {}),
      });
      const res = await api.login({ email: email.trim(), password });
      saveSession(res.access_token, res.user);
      if (linked) {
        // Phiên đã gắn vào tài khoản: chuyển con trỏ sang khoá của tài khoản để /patient/chat tiếp tục cuộc trò chuyện
        saveConsult({ id: linked.id, access_token: linked.token }, res.user.id);
        clearConsult(null);
      }
      setDone(true);
      router.replace(linked ? `/patient/book?consult=${encodeURIComponent(linked.id)}` : "/patient");
    } catch (err) {
      setError(
        errorMessage(
          err,
          linked
            ? "Chưa tạo được tài khoản. Nếu lỗi liên quan đến cuộc trò chuyện, hãy bỏ chọn gắn cuộc trò chuyện và thử lại."
            : "Chưa tạo được tài khoản. Vui lòng thử lại.",
        ),
      );
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-md space-y-6">
      <div className="space-y-1 text-center">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Tạo tài khoản bệnh nhân</h1>
        <p className="text-sm text-slate-500">Để đặt lịch khám và theo dõi kế hoạch tầm soát của bạn.</p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          {consult && (
            <div className="rounded-lg border border-teal-200 bg-teal-50 p-3">
              <label htmlFor="reg-attach" className="flex cursor-pointer items-start gap-2.5 text-sm text-teal-900">
                <input
                  id="reg-attach"
                  type="checkbox"
                  checked={attach}
                  onChange={(e) => setAttach(e.target.checked)}
                  className="mt-0.5 h-4 w-4 accent-teal-700"
                />
                <span>
                  <span className="flex items-center gap-1.5 font-semibold">
                    <MessageSquare className="h-4 w-4" aria-hidden="true" />
                    Gắn cuộc trò chuyện vừa rồi vào hồ sơ
                  </span>
                  <span className="mt-0.5 block text-teal-800">
                    Tuổi, giới, tiền sử gia đình và các thông tin bạn đã chia sẻ được điền sẵn vào hồ sơ để bác sĩ xem trước
                    buổi khám.
                  </span>
                </span>
              </label>
            </div>
          )}
          {consultMissing && (
            <p className="flex items-start gap-2 rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700" role="note">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-slate-500" aria-hidden="true" />
              Không tìm thấy cuộc trò chuyện trên trình duyệt này. Tài khoản vẫn được tạo bình thường; bạn có thể trò
              chuyện lại với trợ lý sau khi đăng nhập.
            </p>
          )}

          <div>
            <label className="label" htmlFor="reg-name">
              Họ và tên
            </label>
            <input
              id="reg-name"
              type="text"
              required
              autoComplete="name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="input"
            />
          </div>
          <div>
            <label className="label" htmlFor="reg-email">
              Email
            </label>
            <input
              id="reg-email"
              type="email"
              required
              autoComplete="email"
              placeholder="ten@example.vn"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="label" htmlFor="reg-password">
                Mật khẩu
              </label>
              <input
                id="reg-password"
                type="password"
                required
                minLength={6}
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                aria-describedby="reg-password-hint"
              />
              <p id="reg-password-hint" className="mt-1 text-xs text-slate-500">
                Tối thiểu 6 ký tự.
              </p>
            </div>
            <div>
              <label className="label" htmlFor="reg-confirm">
                Nhập lại mật khẩu
              </label>
              <input
                id="reg-confirm"
                type="password"
                required
                autoComplete="new-password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className="input"
              />
            </div>
          </div>

          {error && <InlineError message={error} />}
          {done && (
            <p role="status" className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
              <CheckCircle2 className="h-4 w-4 shrink-0" aria-hidden="true" />
              Đã tạo tài khoản. Đang chuyển sang bước đặt lịch…
            </p>
          )}

          <button
            type="submit"
            disabled={loading || done || !fullName.trim() || !email.trim()}
            className="btn-primary w-full"
          >
            {loading ? (
              <>
                <span className="spinner" aria-hidden="true" />
                Đang xử lý…
              </>
            ) : (
              <>
                <UserPlus className="h-4 w-4" aria-hidden="true" />
                {consult && attach ? "Tạo tài khoản và đặt lịch" : "Tạo tài khoản"}
              </>
            )}
          </button>
          <p className="text-xs leading-relaxed text-slate-500">
            Tài khoản đăng ký dành cho bệnh nhân. Bác sĩ được bệnh viện cấp tài khoản riêng. Mật khẩu được mã hoá; bạn chỉ
            xem được dữ liệu của chính mình.
          </p>
        </form>

        <p className="mt-5 text-center text-sm text-slate-600">
          Đã có tài khoản?{" "}
          <Link
            href={consultParam ? `/login?consult=${encodeURIComponent(consultParam)}` : "/login"}
            className="font-semibold text-teal-700 underline-offset-2 hover:underline"
          >
            Đăng nhập
          </Link>
        </p>
      </div>

      <p className="text-center text-sm">
        <Link href="/" className="font-medium text-slate-600 underline-offset-2 hover:text-teal-700 hover:underline">
          Quay lại trò chuyện với trợ lý
        </Link>
      </p>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <main className="flex min-h-screen flex-col bg-slate-50">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center px-4 sm:px-6">
        <Brand />
      </div>
      <div className="flex flex-1 items-start justify-center px-4 pb-10 pt-4 sm:pt-10">
        <Suspense fallback={<div className="skeleton h-96 w-full max-w-md rounded-xl" />}>
          <RegisterForm />
        </Suspense>
      </div>
    </main>
  );
}
