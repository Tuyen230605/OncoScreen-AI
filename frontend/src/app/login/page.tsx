"use client";
import Link from "next/link";
import { FormEvent, Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, USE_MOCK } from "@/lib/api";
import { homeFor, safeNext, saveSession } from "@/lib/auth";
import { anonymousConsultToken, clearConsult, saveConsult } from "@/lib/consult";
import { errorMessage } from "@/lib/errors";
import type { Role } from "@/types/api";
import { Brand } from "@/components/Brand";
import { InlineError } from "@/components/ui";
import { Activity, Info, LogIn, User } from "@/components/icons";

const DEMO_ACCOUNTS: Array<{ label: string; email: string; role: Role }> = [
  { label: "Bệnh nhân đã khám (Lan)", email: "lan@demo.vn", role: "patient" },
  { label: "Bệnh nhân chờ khám (Minh)", email: "minh@demo.vn", role: "patient" },
  { label: "Bác sĩ", email: "doctor@demo.vn", role: "doctor" },
];

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const consultId = params.get("consult");
  const next = safeNext(params.get("next"));

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.login({ email: email.trim(), password });
      saveSession(res.access_token, res.user);
      if (res.user.role === "patient" && consultId) {
        const token = anonymousConsultToken(consultId);
        if (token) {
          try {
            await api.claimConsultation(consultId, token);
            // Phiên đã thuộc tài khoản: /patient/chat tiếp tục đúng cuộc trò chuyện này
            saveConsult({ id: consultId, access_token: token }, res.user.id);
            clearConsult(null);
          } catch {
            /* phiên không gắn được (đã gắn / hết hạn): vẫn cho đặt lịch bình thường */
          }
        }
        router.replace(`/patient/book?consult=${encodeURIComponent(consultId)}`);
        return;
      }
      const home = homeFor(res.user.role);
      router.replace(next && next.startsWith(home) ? next : home);
    } catch (err) {
      setError(errorMessage(err, "Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin."));
      setLoading(false);
    }
  }

  const registerHref = consultId ? `/register?consult=${encodeURIComponent(consultId)}` : "/register";

  return (
    <div className="w-full max-w-md space-y-6">
      <div className="space-y-1 text-center">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Đăng nhập</h1>
        <p className="text-sm text-slate-500">Bệnh nhân và bác sĩ dùng chung cổng đăng nhập.</p>
      </div>

      {consultId && (
        <p className="flex items-start gap-2 rounded-lg border border-teal-200 bg-teal-50 p-3 text-sm text-teal-900" role="note">
          <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          Sau khi đăng nhập, cuộc trò chuyện vừa rồi sẽ được gắn vào hồ sơ của bạn để đặt lịch.
        </p>
      )}

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="label" htmlFor="login-email">
              Email
            </label>
            <input
              id="login-email"
              type="email"
              required
              autoComplete="email"
              placeholder="ten@example.vn"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
            />
          </div>
          <div>
            <label className="label" htmlFor="login-password">
              Mật khẩu
            </label>
            <input
              id="login-password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
            />
          </div>
          {error && <InlineError message={error} />}
          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? (
              <>
                <span className="spinner" aria-hidden="true" />
                Đang xử lý…
              </>
            ) : (
              <>
                <LogIn className="h-4 w-4" aria-hidden="true" />
                Đăng nhập
              </>
            )}
          </button>
        </form>

        <p className="mt-5 text-center text-sm text-slate-600">
          Chưa có tài khoản?{" "}
          <Link href={registerHref} className="font-semibold text-teal-700 underline-offset-2 hover:underline">
            Đăng ký bệnh nhân
          </Link>
        </p>

        {USE_MOCK && (
          <div className="mt-6 border-t border-slate-100 pt-5">
            <p className="mb-3 text-center text-xs font-medium text-slate-500">Tài khoản demo (mật khẩu 123456)</p>
            <div className="grid grid-cols-1 gap-2">
              {DEMO_ACCOUNTS.map((acc) => (
                <button
                  key={acc.email}
                  type="button"
                  onClick={() => {
                    setEmail(acc.email);
                    setPassword("123456");
                    setError(null);
                  }}
                  className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-200 p-2.5 text-left text-sm font-medium text-slate-700 transition-colors hover:border-teal-500 hover:bg-teal-50"
                >
                  {acc.role === "doctor" ? (
                    <Activity className="h-4 w-4 shrink-0 text-indigo-600" aria-hidden="true" />
                  ) : (
                    <User className="h-4 w-4 shrink-0 text-teal-600" aria-hidden="true" />
                  )}
                  <span className="truncate">{acc.label}</span>
                  <span className="ml-auto truncate text-xs text-slate-500">{acc.email}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      <p className="text-center text-sm">
        <Link href="/" className="font-medium text-slate-600 underline-offset-2 hover:text-teal-700 hover:underline">
          Quay lại trò chuyện với trợ lý
        </Link>
      </p>
    </div>
  );
}

export default function LoginPage() {
  return (
    <main className="flex min-h-screen flex-col bg-slate-50">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center px-4 sm:px-6">
        <Brand />
      </div>
      <div className="flex flex-1 items-start justify-center px-4 pb-10 pt-4 sm:pt-10">
        <Suspense fallback={<div className="skeleton h-96 w-full max-w-md rounded-xl" />}>
          <LoginForm />
        </Suspense>
      </div>
    </main>
  );
}
