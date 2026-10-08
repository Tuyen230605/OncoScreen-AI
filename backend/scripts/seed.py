"""Seed tài khoản demo: python scripts/seed.py (chạy từ thư mục backend)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal, init_db  # noqa: E402
from app.models import PatientProfile  # noqa: E402
from app.schemas.auth import RegisterIn  # noqa: E402
from app.services import auth_service  # noqa: E402

DEMO = [
    ("doctor@demo.vn", "BS. Nguyễn Văn A", "doctor", None),
    (
        "lan@demo.vn",
        "Trần Thị Lan",
        "patient",
        dict(age=45, gender="female", genetics_history=["breast_cancer_mother"]),
    ),
    (
        "hung@demo.vn",
        "Lê Văn Hùng",
        "patient",
        dict(age=55, gender="male", lifestyle={"smoking": True, "pack_years": 30}),
    ),
]

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    init_db()
    db = SessionLocal()
    for email, name, role, profile in DEMO:
        user = auth_service.get_by_email(db, email)
        if not user:
            user = auth_service.create_user(db, RegisterIn(email=email, password="123456", full_name=name, role=role))
            print("created", email)
        if profile and not db.get(PatientProfile, user.id):
            db.add(PatientProfile(user_id=user.id, **profile))
            db.commit()
    db.close()
    print("Seed xong. Mat khau chung: 123456")

