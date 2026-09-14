"""Fixtures: SQLite file tạm + TestClient + MockAgent."""

from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["USE_MOCK_AGENT"] = "true"
os.environ["SECRET_KEY"] = "test"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def register_and_login(client: TestClient, email: str, role: str) -> dict:
    client.post("/api/v1/auth/register", json={"email": email, "password": "123456", "full_name": email, "role": role})
    tok = client.post("/api/v1/auth/login", json={"email": email, "password": "123456"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture()
def patient(client):
    h = register_and_login(client, "lan@test.vn", "patient")
    client.put(
        "/api/v1/patients/me/profile",
        json={"age": 45, "gender": "female", "genetics_history": ["breast_cancer_mother"], "lifestyle": {}},
        headers=h,
    )
    return h


@pytest.fixture()
def doctor(client):
    return register_and_login(client, "doc@test.vn", "doctor")


NORMAL_ANSWERS = [
    {"question_id": "family_history", "value": ["Ung thư vú"]},
    {"question_id": "smoking", "value": False},
    {"question_id": "alcohol", "value": "Không"},
    {"question_id": "hbv_hcv", "value": False},
    {"question_id": "symptom_lump", "value": False},
    {"question_id": "symptom_bleeding", "value": False},
    {"question_id": "symptom_weight_loss", "value": False},
    {"question_id": "symptom_persistent_pain", "value": False},
]
