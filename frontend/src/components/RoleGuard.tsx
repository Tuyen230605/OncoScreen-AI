"use client";
import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { Role } from "@/types/api";
import { clearSession, getUser, homeFor, loginHref, onSessionExpired } from "@/lib/auth";
import { Brand, SiteFooter } from "@/components/Brand";
import {
  Bell,
  BookOpen,
  CalendarPlus,
  ClipboardList,
  History,
  LayoutDashboard,
  LogOut,
  MessageSquare,
  UserCircle,
  Users,
  type IconType,
} from "@/components/icons";

interface NavItem {
  href: string;
  label: string;
  icon: IconType;
  /** Các tiền tố đường dẫn cũng được tính là mục này (vd. trang chi tiết). */
  match?: string[];
}

const PATIENT_NAV: NavItem[] = [
  { href: "/patient", label: "Tổng quan", icon: LayoutDashboard, match: ["/patient/visits"] },
  { href: "/patient/chat", label: "Trợ lý tầm soát", icon: MessageSquare },
  { href: "/patient/book", label: "Đặt lịch", icon: CalendarPlus },
  { href: "/patient/record", label: "Hồ sơ xuyên suốt", icon: History },
  { href: "/patient/reminders", label: "Nhắc lịch", icon: Bell },
  { href: "/patient/education", label: "Tài liệu", icon: BookOpen },
  { href: "/patient/profile", label: "Thông tin sức khoẻ", icon: UserCircle },
];

const DOCTOR_NAV: NavItem[] = [
  { href: "/doctor", label: "Hàng chờ khám", icon: ClipboardList, match: ["/doctor/encounters"] },
  { href: "/doctor/patients", label: "Bệnh nhân", icon: Users },
];

function isActive(pathname: string, item: NavItem): boolean {
  if (pathname === item.href) return true;
  if (item.match?.some((p) => pathname.startsWith(p))) return true;
  const isRoot = item.href === "/patient" || item.href === "/doctor";
  return !isRoot && pathname.startsWith(`${item.href}/`);
}

const currentPath = () => `${window.location.pathname}${window.location.search}`;

/**
 * Khung trang theo vai trò:
 * - Chưa đăng nhập → /login?next=<trang hiện tại>
 * - Sai vai trò → về trang của vai trò đó
 * - JWT hết hạn giữa chừng (API trả 401, phiên đã bị xoá) → /login?next=<trang hiện tại>
 */
export function RoleGuard({ role, children }: { role: Role; children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [ok, setOk] = useState(false);
  const [userName, setUserName] = useState("");

  useEffect(() => {
    const u = getUser();
    if (!u) {
      router.replace(loginHref(currentPath()));
    } else if (u.role !== role) {
      router.replace(homeFor(u.role));
    } else {
      setUserName(u.full_name);
      setOk(true);
    }
  }, [role, router]);

  useEffect(
    () =>
      onSessionExpired(() => {
        setOk(false);
        router.replace(loginHref(currentPath()));
      }),
    [router],
  );

  function handleLogout() {
    clearSession();
    router.replace("/");
  }

  if (!ok) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="w-full max-w-md space-y-3 px-4" aria-busy="true" aria-label="Đang tải">
          <div className="skeleton h-8 w-40" />
          <div className="skeleton h-24 rounded-xl" />
          <div className="skeleton h-24 rounded-xl" />
        </div>
      </div>
    );
  }

  const isDoctor = role === "doctor";
  const navItems = isDoctor ? DOCTOR_NAV : PATIENT_NAV;
  const activeNavClass = isDoctor ? "bg-indigo-50 text-indigo-700 font-semibold" : "bg-teal-50 text-teal-800 font-semibold";
  const activeIcon = isDoctor ? "text-indigo-600" : "text-teal-700";
  const roleBadgeClass = isDoctor
    ? "bg-indigo-100 text-indigo-800 border border-indigo-200"
    : "bg-teal-100 text-teal-800 border border-teal-200";

  const nav = (
    <nav className="flex min-w-0 items-center gap-1 overflow-x-auto py-1" aria-label="Điều hướng chính">
      {navItems.map((item) => {
        const active = isActive(pathname, item);
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              active ? activeNavClass : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            }`}
            aria-current={active ? "page" : undefined}
          >
            <Icon className={`h-4 w-4 ${active ? activeIcon : "text-slate-500"}`} aria-hidden />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/95 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center gap-4 px-4 sm:px-6">
          <Brand
            href={homeFor(role)}
            tone={isDoctor ? "doctor" : "patient"}
            subtitle={isDoctor ? "Cổng bác sĩ" : "Cổng bệnh nhân"}
          />
          <div className="hidden min-w-0 flex-1 lg:block">{nav}</div>
          <div className="ml-auto flex items-center gap-3">
            <div className="hidden flex-col items-end text-right sm:flex">
              <span className="max-w-[12rem] truncate text-sm font-semibold leading-tight text-slate-900">{userName}</span>
              <span className={`badge mt-0.5 text-[10px] ${roleBadgeClass}`}>{isDoctor ? "Bác sĩ" : "Bệnh nhân"}</span>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="btn-ghost px-2.5 text-sm text-slate-600"
              aria-label="Đăng xuất"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">Đăng xuất</span>
            </button>
          </div>
        </div>
        <div className="mx-auto max-w-6xl border-t border-slate-100 px-2 sm:px-4 lg:hidden">{nav}</div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6 sm:py-8">{children}</main>
      <SiteFooter />
    </div>
  );
}
