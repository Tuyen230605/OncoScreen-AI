"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { homeFor, saveSession } from "@/lib/auth";

/** TODO(FE): thêm tab Đăng ký (api.register), hiển thị lỗi đẹp hơn. */
export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("lan@demo.vn");
  const [password, setPassword] = useState("123456");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const res = await api.login({ email, password });
      saveSession(res.access_token, res.user);
      router.replace(homeFor(res.user.role));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đăng nhập thất bại");
    }
  }

  return (
    <main className="mx-auto mt-20 max-w-sm rounded-xl bg-white p-6 shadow">
      <h1 className="mb-1 text-xl font-semibold">OncoScreen AI</h1>
      <p className="mb-4 text-sm text-slate-500">Đăng nhập (bệnh nhân hoặc bác sĩ)</p>
      <form onSubmit={onSubmit} className="space-y-3">
        <input className="w-full rounded border p-2" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" />
        <input className="w-full rounded border p-2" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Mật khẩu" />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="w-full rounded bg-blue-600 p-2 text-white">Đăng nhập</button>
      </form>
      <p className="mt-4 text-xs text-slate-400">Demo: lan@demo.vn / doctor@demo.vn — mật khẩu 123456</p>
    </main>
  );
}
