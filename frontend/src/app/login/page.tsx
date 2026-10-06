"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Role } from "@/types/api";
import { homeFor, saveSession } from "@/lib/auth";

type Tab = "login" | "register";

const DEMO_ACCOUNTS = [
  { label: "Bệnh nhân demo", email: "lan@demo.vn", password: "123456", role: "patient" as Role },
  { label: "Bác sĩ demo", email: "doctor@demo.vn", password: "123456", role: "doctor" as Role },
];

export default function LoginPage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("login");

  // --- Login state ---
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loginLoading, setLoginLoading] = useState(false);

  // --- Register state ---
  const [regFullName, setRegFullName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regRole, setRegRole] = useState<Role>("patient");
  const [regError, setRegError] = useState<string | null>(null);
  const [regLoading, setRegLoading] = useState(false);
  const [regSuccess, setRegSuccess] = useState(false);

  async function handleLogin(e: FormEvent) {
    e.preventDefault();
    setLoginError(null);
    setLoginLoading(true);
    try {
      const res = await api.login({ email: loginEmail, password: loginPassword });
      saveSession(res.access_token, res.user);
      router.replace(homeFor(res.user.role));
    } catch (err) {
      setLoginError(err instanceof Error ? err.message : "Đăng nhập thất bại. Vui lòng thử lại.");
    } finally {
      setLoginLoading(false);
    }
  }

  async function handleRegister(e: FormEvent) {
    e.preventDefault();
    setRegError(null);
    setRegLoading(true);
    try {
      await api.register({
        email: regEmail,
        password: regPassword,
        full_name: regFullName,
        role: regRole,
      });
      setRegSuccess(true);
      // Tự chuyển sang tab đăng nhập, điền sẵn email
      setTimeout(() => {
        setTab("login");
        setLoginEmail(regEmail);
        setLoginPassword(regPassword);
        setRegSuccess(false);
        setRegFullName("");
        setRegEmail("");
        setRegPassword("");
      }, 1500);
    } catch (err) {
      setRegError(err instanceof Error ? err.message : "Đăng ký thất bại. Vui lòng thử lại.");
    } finally {
      setRegLoading(false);
    }
  }

  function fillDemo(account: (typeof DEMO_ACCOUNTS)[0]) {
    setLoginEmail(account.email);
    setLoginPassword(account.password);
    setLoginError(null);
    setTab("login");
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-blue-50 via-white to-slate-100 p-4">
      {/* Logo / brand */}
      <div className="mb-8 text-center fade-in">
        <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600 shadow-lg shadow-blue-200">
          <svg viewBox="0 0 24 24" fill="none" className="h-8 w-8 text-white" aria-hidden="true">
            <path
              d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2v-5h2v5zm0-7h-2V7h2v2z"
              fill="currentColor"
            />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-slate-900">OncoScreen AI</h1>
        <p className="mt-1 text-sm text-slate-500">Hỗ trợ tầm soát ung thư có bác sĩ phê duyệt</p>
      </div>

      {/* Card */}
      <div className="w-full max-w-sm fade-in">
        <div className="card-padded">
          {/* Tabs */}
          <div className="mb-5 flex rounded-lg border border-slate-200 bg-slate-50 p-1">
            <button
              id="tab-login"
              type="button"
              className={`flex-1 rounded-md py-1.5 text-sm font-medium transition-all ${
                tab === "login" ? "bg-white text-blue-600 shadow-sm" : "text-slate-500 hover:text-slate-700"
              }`}
              onClick={() => setTab("login")}
            >
              Đăng nhập
            </button>
            <button
              id="tab-register"
              type="button"
              className={`flex-1 rounded-md py-1.5 text-sm font-medium transition-all ${
                tab === "register" ? "bg-white text-blue-600 shadow-sm" : "text-slate-500 hover:text-slate-700"
              }`}
              onClick={() => setTab("register")}
            >
              Đăng ký
            </button>
          </div>

          {/* ===== Đăng nhập ===== */}
          {tab === "login" && (
            <form id="form-login" onSubmit={handleLogin} className="space-y-4 fade-in">
              <div>
                <label htmlFor="login-email" className="label">Email</label>
                <input
                  id="login-email"
                  type="email"
                  autoComplete="email"
                  required
                  className={`input ${loginError ? "input-error" : ""}`}
                  placeholder="email@example.com"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="login-password" className="label">Mật khẩu</label>
                <input
                  id="login-password"
                  type="password"
                  autoComplete="current-password"
                  required
                  className={`input ${loginError ? "input-error" : ""}`}
                  placeholder="••••••••"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                />
              </div>
              {loginError && (
                <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600 fade-in">
                  {loginError}
                </p>
              )}
              <button
                id="btn-login-submit"
                type="submit"
                disabled={loginLoading}
                className="btn-primary w-full"
              >
                {loginLoading ? <span className="spinner" aria-hidden="true" /> : null}
                {loginLoading ? "Đang đăng nhập…" : "Đăng nhập"}
              </button>
            </form>
          )}

          {/* ===== Đăng ký ===== */}
          {tab === "register" && (
            <form id="form-register" onSubmit={handleRegister} className="space-y-4 fade-in">
              <div>
                <label htmlFor="reg-fullname" className="label">Họ và tên</label>
                <input
                  id="reg-fullname"
                  type="text"
                  autoComplete="name"
                  required
                  className="input"
                  placeholder="Nguyễn Thị Lan"
                  value={regFullName}
                  onChange={(e) => setRegFullName(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="reg-email" className="label">Email</label>
                <input
                  id="reg-email"
                  type="email"
                  autoComplete="email"
                  required
                  className="input"
                  placeholder="email@example.com"
                  value={regEmail}
                  onChange={(e) => setRegEmail(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="reg-password" className="label">Mật khẩu</label>
                <input
                  id="reg-password"
                  type="password"
                  autoComplete="new-password"
                  required
                  minLength={6}
                  className="input"
                  placeholder="Tối thiểu 6 ký tự"
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                />
              </div>
              <div>
                <label className="label">Vai trò</label>
                <div className="flex gap-3">
                  {(["patient", "doctor"] as Role[]).map((r) => (
                    <label
                      key={r}
                      className={`flex flex-1 cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors ${
                        regRole === r
                          ? "border-blue-500 bg-blue-50 text-blue-700"
                          : "border-slate-200 text-slate-600 hover:bg-slate-50"
                      }`}
                    >
                      <input
                        type="radio"
                        name="role"
                        value={r}
                        checked={regRole === r}
                        onChange={() => setRegRole(r)}
                        className="sr-only"
                      />
                      <span>{r === "patient" ? "🏥 Bệnh nhân" : "🩺 Bác sĩ"}</span>
                    </label>
                  ))}
                </div>
              </div>
              {regError && (
                <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600 fade-in">
                  {regError}
                </p>
              )}
              {regSuccess && (
                <p role="status" className="rounded-lg bg-green-50 px-3 py-2 text-sm text-green-700 fade-in">
                  ✓ Đăng ký thành công! Đang chuyển sang đăng nhập…
                </p>
              )}
              <button
                id="btn-register-submit"
                type="submit"
                disabled={regLoading || regSuccess}
                className="btn-primary w-full"
              >
                {regLoading ? <span className="spinner" aria-hidden="true" /> : null}
                {regLoading ? "Đang đăng ký…" : "Tạo tài khoản"}
              </button>
            </form>
          )}
        </div>

        {/* Demo accounts */}
        <div className="mt-4 rounded-xl border border-slate-200 bg-white/60 p-4 backdrop-blur-sm">
          <p className="mb-2.5 text-xs font-medium text-slate-400 uppercase tracking-wide">Đăng nhập nhanh (demo)</p>
          <div className="flex gap-2">
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.email}
                id={`btn-demo-${acc.role}`}
                type="button"
                onClick={() => fillDemo(acc)}
                className="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-xs text-slate-600 shadow-sm transition hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700"
              >
                <span className="block font-medium">{acc.label}</span>
                <span className="text-slate-400">{acc.email}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Disclaimer nhỏ */}
      <p className="mt-8 max-w-xs text-center text-xs text-slate-400">
        OncoScreen AI chỉ hỗ trợ tư vấn tầm soát, <strong>không chẩn đoán bệnh</strong>. Mọi kết quả phải được bác sĩ phê duyệt trước khi bệnh nhân xem.
      </p>
    </main>
  );
}
