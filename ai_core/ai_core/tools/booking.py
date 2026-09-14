"""Tool: booking (mô phỏng) — tính ngày hẹn kế tiếp từ interval và lần thực hiện gần nhất."""

from __future__ import annotations

from datetime import date, timedelta


def next_due_date(last_done: date | None, interval_months: int, today: date | None = None) -> date:
    today = today or date.today()
    if last_done is None:
        return today + timedelta(days=30)  # lần đầu: hẹn trong ~1 tháng
    # xấp xỉ tháng = 30 ngày; đủ cho mô phỏng
    due = last_done + timedelta(days=30 * interval_months)
    return max(due, today)
