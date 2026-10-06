"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getUser, homeFor } from "@/lib/auth";

/** Trang gốc: redirect theo role, chưa login → /login */
export default function Home() {
  const router = useRouter();
  useEffect(() => {
    const u = getUser();
    router.replace(u ? homeFor(u.role) : "/login");
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <span className="spinner h-6 w-6 text-blue-500" aria-label="Đang tải…" />
    </div>
  );
}
