"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import type { Role } from "@/types/api";
import { clearSession, getUser, homeFor } from "@/lib/auth";

interface NavItem {
  href: string;
  label: string;
  icon: string;
}

const PATIENT_NAV: NavItem[] = [
  { href: "/patient", label: "Tổng quan", icon: "🏠" },
  { href: "/patient/profile", label: "Hồ sơ", icon: "👤" },
  { href: "/patient/reminders", label: "Nhắc lịch", icon: "🔔" },
];

const DOCTOR_NAV: NavItem[] = [
  { href: "/doctor", label: "Hàng chờ duyệt", icon: "📋" },
];

/**
 * Bọc layout theo role:
 * - Chưa đăng nhập → /login
 * - Sai role → về trang của role đó
 */
export function RoleGuard({ role, children }: { role: Role; children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ok, setOk] = useState(false);
  const [userName, setUserName] = useState("");

  useEffect(() => {
    const u = getUser();
    if (!u) {
      router.replace("/login");
    } else if (u.role !== role) {
      router.replace(homeFor(u.role));
    } else {
      setUserName(u.full_name);
      setOk(true);
    }
  }, [role, router]);

  function handleLogout() {
    clearSession();
    router.replace("/login");
  }

  if (!ok) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <span className="spinner h-6 w-6 text-blue-500" aria-label="Đang tải…" />
      </div>
    );
  }

  const navItems = role === "doctor" ? DOCTOR_NAV : PATIENT_NAV;
  const roleBadge = role === "doctor" ? "Bác sĩ" : "Bệnh nhân";
  const roleBadgeClass =
    role === "doctor"
      ? "bg-violet-100 text-violet-700"
      : "bg-blue-100 text-blue-700";

  return (
    <div className="flex min-h-screen flex-col bg-slate-100">
      {/* ===== Top Navbar ===== */}
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-6xl items-center gap-4 px-4">
          {/* Logo */}
          <Link href={homeFor(role)} className="flex items-center gap-2 font-bold text-slate-900 hover:text-blue-600 transition-colors">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-600 text-white text-xs font-bold">OS</span>
            <span className="hidden sm:inline">OncoScreen AI</span>
          </Link>

          {/* Nav links */}
          <nav className="flex flex-1 items-center gap-1" aria-label="Điều hướng chính">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-blue-50 text-blue-600"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                  aria-current={isActive ? "page" : undefined}
                >
                  <span aria-hidden="true">{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* User info + logout */}
          <div className="flex items-center gap-3">
            <div className="hidden flex-col items-end text-right sm:flex">
              <span className="text-sm font-medium text-slate-800 leading-tight">{userName}</span>
              <span className={`badge text-[10px] ${roleBadgeClass}`}>{roleBadge}</span>
            </div>
            <button
              id="btn-logout"
              type="button"
              onClick={handleLogout}
              className="btn-ghost text-xs"
              title="Đăng xuất"
            >
              Đăng xuất
            </button>
          </div>
        </div>
      </header>

      {/* ===== Page content ===== */}
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">{children}</main>

      {/* ===== Footer ===== */}
      <footer className="border-t border-slate-200 bg-white py-3 text-center text-xs text-slate-400">
        OncoScreen AI — chỉ hỗ trợ tầm soát, <strong className="font-medium">không chẩn đoán bệnh</strong>. Mọi kết quả được bác sĩ phê duyệt trước khi hiển thị.
      </footer>
    </div>
  );
}
