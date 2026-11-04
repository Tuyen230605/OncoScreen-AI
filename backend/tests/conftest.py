"""Fixtures: SQLite file tạm + TestClient + MockAgent (pipeline thật, không gọi LLM)."""

from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["USE_MOCK_AGENT"] = "true"
os.environ["SECRET_KEY"] = "test"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

API = "/api/v1"


@pytest.fixture(autouse=True)
def _fresh_db():
    from app.services.navigator_service import create_limiter

    create_limiter.reset()  # limiter nằm trong bộ nhớ tiến trình: mỗi test bắt đầu với bộ đếm sạch
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def login(client: TestClient, email: str) -> dict:
    tok = client.post(f"{API}/auth/login", json={"email": email, "password": "123456"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def register_and_login(client: TestClient, email: str, role: str = "patient", **extra) -> dict:
    if role == "doctor":
        from app.database import SessionLocal
        from app.schemas.auth import RegisterIn
        from app.services import auth_service

        with SessionLocal() as db:
            auth_service.create_user(db, RegisterIn(email=email, password="123456", full_name=email, role="doctor"))
    else:
        r = client.post(
            f"{API}/auth/register",
            json={"email": email, "password": "123456", "full_name": email, "role": role, **extra},
        )
        assert r.status_code == 201, r.text
    return login(client, email)


def start_consultation(client: TestClient, headers: dict | None = None) -> tuple[str, dict]:
    r = client.post(f"{API}/navigator/consultations", headers=headers or {})
    assert r.status_code == 201, r.text
    body = r.json()
    return body["consultation"]["id"], {**(headers or {}), "X-Consult-Token": body["access_token"]}


def say(client: TestClient, consult_id: str, headers: dict, message: str | None = None, answers=None) -> dict:
    payload = {"message": message} if message else {}
    if answers:
        payload["answers"] = answers
    r = client.post(f"{API}/navigator/consultations/{consult_id}/messages", json=payload, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture()
def doctor(client):
    return register_and_login(client, "doc@test.vn", "doctor")
