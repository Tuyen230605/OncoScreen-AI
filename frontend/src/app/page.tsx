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
  return null;
}
