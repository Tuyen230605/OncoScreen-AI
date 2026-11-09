"""Rate limit tạo phiên Navigator công khai (chống tạo hàng loạt phiên → tốn chi phí LLM)."""

import pytest

from app.config import settings
from app.core.rate_limit import SlidingWindowLimiter, retry_after_header
from tests.conftest import API, register_and_login


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_limiter_allows_up_to_limit_then_blocks_until_window_slides():
    clock = _Clock()
    limiter = SlidingWindowLimiter(clock)
    assert [limiter.hit("a", 3, 60) for _ in range(3)] == [None, None, None]
    wait = limiter.hit("a", 3, 60)
    assert wait == pytest.approx(60)
    assert limiter.hit("b", 3, 60) is None  # key khác không bị ảnh hưởng
    clock.now += 30
    assert limiter.hit("a", 3, 60) == pytest.approx(30)  # lượt bị từ chối không kéo dài thời gian chờ
    clock.now += 30.001
    assert limiter.hit("a", 3, 60) is None


def test_limiter_disabled_when_limit_not_positive():
    limiter = SlidingWindowLimiter(_Clock())
    assert all(limiter.hit("a", 0, 60) is None for _ in range(100))


def test_limiter_evicts_expired_keys(monkeypatch):
    from app.core import rate_limit

    monkeypatch.setattr(rate_limit, "MAX_TRACKED_KEYS", 5)
    clock = _Clock()
    limiter = SlidingWindowLimiter(clock)
    for i in range(5):
        limiter.hit(f"old{i}", 1, 10)
    clock.now += 11
    limiter.hit("new1", 1, 10)
    assert set(limiter._hits) == {"new1"}  # vượt ngưỡng 5 key → key đã hết hạn bị dọn


def test_retry_after_header_rounds_up_to_whole_seconds():
    assert retry_after_header(0.2) == {"Retry-After": "1"}
    assert retry_after_header(59.1) == {"Retry-After": "60"}


def test_anonymous_consultation_creation_is_rate_limited(client, monkeypatch):
    monkeypatch.setattr(settings, "consult_create_limit", 3)
    for _ in range(3):
        assert client.post(f"{API}/navigator/consultations").status_code == 201
    blocked = client.post(f"{API}/navigator/consultations")
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) >= 1
    assert "quá nhiều phiên" in blocked.json()["detail"]


def test_logged_in_patient_has_own_quota(client, monkeypatch):
    monkeypatch.setattr(settings, "consult_create_limit", 2)
    for _ in range(2):
        assert client.post(f"{API}/navigator/consultations").status_code == 201
    assert client.post(f"{API}/navigator/consultations").status_code == 429  # IP đã hết lượt ẩn danh
    patient = register_and_login(client, "lan@test.vn")
    assert client.post(f"{API}/navigator/consultations", headers=patient).status_code == 201
    assert client.post(f"{API}/navigator/consultations", headers=patient).status_code == 201
    assert client.post(f"{API}/navigator/consultations", headers=patient).status_code == 429


def test_rate_limit_does_not_affect_messages_in_existing_consultation(client, monkeypatch):
    monkeypatch.setattr(settings, "consult_create_limit", 1)
    r = client.post(f"{API}/navigator/consultations")
    cid, token = r.json()["consultation"]["id"], r.json()["access_token"]
    assert client.post(f"{API}/navigator/consultations").status_code == 429
    msg = client.post(
        f"{API}/navigator/consultations/{cid}/messages",
        json={"message": "Tôi là nữ 45 tuổi"},
        headers={"X-Consult-Token": token},
    )
    assert msg.status_code == 200
