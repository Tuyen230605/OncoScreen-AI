"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { Role } from "@/types/api";
import { clearSession, getUser, homeFor } from "@/lib/auth";

/** Bọc layout theo role: chưa login → /login; sai role → về trang của role đó. */
export function RoleGuard({ role, children }: { role: Role; children: React.ReactNode }) {
  const router = useRouter();
  const [ok, setOk] = useState(false);
  useEffect(() => {
    const u = getUser();
    if (!u) router.replace("/login");
    else if (u.role !== role) router.replace(homeFor(u.role));
    else setOk(true);
  }, [role, router]);
  if (!ok) return null;
  return (
    <div className="mx-auto max-w-5xl p-4">
      <header className="mb-4 flex items-center justify-between">
        <span className="font-semibold">OncoScreen AI · {role === "doctor" ? "Bác sĩ" : "Bệnh nhân"}</span>
        <button className="text-sm text-slate-500 underline" onClick={() => { clearSession(); router.replace("/login"); }}>
          Đăng xuất
        </button>
      </header>
      {children}
    </div>
  );
}
