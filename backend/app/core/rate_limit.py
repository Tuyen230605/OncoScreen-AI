"""Giới hạn tần suất sliding-window trong bộ nhớ tiến trình.

Đủ cho triển khai local một tiến trình (đồ án). Chạy nhiều worker/instance thì mỗi tiến trình đếm riêng —
khi đó cần kho dùng chung (Redis) hoặc giới hạn ở reverse proxy.
"""

from __future__ import annotations

import math
import threading
from collections import deque
from collections.abc import Callable
from time import monotonic

MAX_TRACKED_KEYS = 10_000


class SlidingWindowLimiter:
    def __init__(self, clock: Callable[[], float] = monotonic) -> None:
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window_seconds: float) -> float | None:
        """Ghi nhận một lượt cho `key`. Trả None nếu được phép; ngược lại trả số giây cần chờ (> 0).

        `limit <= 0` tắt giới hạn. Lượt bị từ chối không được tính (không kéo dài thời gian chờ).
        """
        if limit <= 0:
            return None
        now = self._clock()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= now - window_seconds:
                hits.popleft()
            if len(hits) >= limit:
                return max(hits[0] + window_seconds - now, 0.001)
            hits.append(now)
            if len(self._hits) > MAX_TRACKED_KEYS:
                self._evict(now, window_seconds)
            return None

    def _evict(self, now: float, window_seconds: float) -> None:
        """Bỏ key đã hết hạn để bộ nhớ không phình khi có nhiều IP khác nhau."""
        for key in [k for k, h in self._hits.items() if not h or h[-1] <= now - window_seconds]:
            del self._hits[key]

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


def retry_after_header(wait_seconds: float) -> dict[str, str]:
    return {"Retry-After": str(max(1, math.ceil(wait_seconds)))}
