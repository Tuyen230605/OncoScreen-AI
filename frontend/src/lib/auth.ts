/** Lưu token + user ở localStorage (đủ cho demo local). Mọi truy cập localStorage đều bọc try/catch. */
import type { UserOut } from "@/types/api";

const TOKEN_KEY = "cs_token";
const USER_KEY = "cs_user";

function storage(): Storage | null {
  try {
    return typeof window !== "undefined" ? window.localStorage : null;
  } catch {
    return null;
  }
}

export function getToken(): string | null {
  try {
    return storage()?.getItem(TOKEN_KEY) ?? null;
  } catch {
    return null;
  }
}

export function getUser(): UserOut | null {
  try {
    const raw = storage()?.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as UserOut) : null;
  } catch {
    return null;
  }
}

export function saveSession(token: string, user: UserOut): void {
  try {
    storage()?.setItem(TOKEN_KEY, token);
    storage()?.setItem(USER_KEY, JSON.stringify(user));
  } catch {
    /* storage bị chặn: phiên chỉ tồn tại trong bộ nhớ trình duyệt hiện tại */
  }
}

export function clearSession(): void {
  try {
    storage()?.removeItem(TOKEN_KEY);
    storage()?.removeItem(USER_KEY);
  } catch {
    /* ignore */
  }
}

const SESSION_EXPIRED_EVENT = "cs:session-expired";

/**
 * Backend từ chối JWT `token` (hết hạn / không hợp lệ): xoá phiên và báo cho các component đang mở
 * (RoleGuard chuyển về /login, Navigator chuyển sang chế độ ẩn danh). Bỏ qua nếu đã đăng nhập phiên khác.
 */
export function expireSession(token: string): void {
  if (getToken() !== token) return;
  clearSession();
  try {
    window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
  } catch {
    /* ngoài trình duyệt */
  }
}

/** Đăng ký nghe sự kiện phiên hết hạn; trả hàm huỷ đăng ký (dùng trực tiếp làm cleanup của useEffect). */
export function onSessionExpired(listener: () => void): () => void {
  if (typeof window === "undefined") return () => undefined;
  window.addEventListener(SESSION_EXPIRED_EVENT, listener);
  return () => window.removeEventListener(SESSION_EXPIRED_EVENT, listener);
}

/** Trang đăng nhập, quay lại `next` (đường dẫn hiện tại) sau khi đăng nhập. */
export function loginHref(next: string): string {
  return `/login?next=${encodeURIComponent(next)}`;
}

export function homeFor(role: UserOut["role"]): string {
  return role === "doctor" ? "/doctor" : "/patient";
}

/** Chỉ cho phép đường dẫn nội bộ khi redirect sau đăng nhập (tránh open redirect). */
export function safeNext(next: string | null | undefined): string | null {
  if (!next || !next.startsWith("/") || next.startsWith("//")) return null;
  return next;
}
