"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import type { UserOut } from "@/types/api";
import { getUser, homeFor, onSessionExpired } from "@/lib/auth";
import { Brand } from "@/components/Brand";
import { LayoutDashboard, LogIn, UserPlus } from "@/components/icons";

/** Header trang công khai: Đăng nhập / Đăng ký, hoặc lối vào trang cá nhân nếu đã đăng nhập. */
export function PublicHeader() {
  const [user, setUser] = useState<UserOut | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setUser(getUser());
    setReady(true);
  }, []);

  // Phiên đăng nhập hết hạn khi đang ở trang công khai → hiện lại nút Đăng nhập / Đăng ký
  useEffect(() => onSessionExpired(() => setUser(null)), []);

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/95 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-3 px-4 sm:px-6">
        <Brand />
        <nav className="flex items-center gap-2" aria-label="Tài khoản">
          {!ready ? (
            <div className="skeleton h-9 w-36 rounded-lg" aria-hidden="true" />
          ) : user ? (
            <Link href={homeFor(user.role)} className={user.role === "doctor" ? "btn-doctor" : "btn-primary"}>
              <LayoutDashboard className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">{user.role === "doctor" ? "Cổng bác sĩ" : "Trang của tôi"}</span>
              <span className="sm:hidden">Vào trang</span>
            </Link>
          ) : (
            <>
              <Link href="/login" className="btn-ghost px-3">
                <LogIn className="h-4 w-4" aria-hidden="true" />
                Đăng nhập
              </Link>
              <Link href="/register" className="btn-primary px-3">
                <UserPlus className="h-4 w-4" aria-hidden="true" />
                Đăng ký
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
