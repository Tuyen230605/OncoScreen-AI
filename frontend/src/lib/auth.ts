/** Lưu token + user ở localStorage (đủ cho demo local). */
import type { UserOut } from "@/types/api";

const TOKEN_KEY = "cs_token";
const USER_KEY = "cs_user";
const isBrowser = () => typeof window !== "undefined";

export function getToken(): string | null {
  return isBrowser() ? localStorage.getItem(TOKEN_KEY) : null;
}
export function getUser(): UserOut | null {
  if (!isBrowser()) return null;
  const raw = localStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as UserOut) : null;
}
export function saveSession(token: string, user: UserOut): void {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}
export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
export function homeFor(role: UserOut["role"]): string {
  return role === "doctor" ? "/doctor" : "/patient";
}
