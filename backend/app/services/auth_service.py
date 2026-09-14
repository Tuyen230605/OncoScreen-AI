from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.auth import RegisterIn


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def create_user(db: Session, body: RegisterIn) -> User:
    user = User(
        email=body.email.lower(), password_hash=hash_password(body.password), full_name=body.full_name, role=body.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = get_by_email(db, email)
    if user and verify_password(password, user.password_hash):
        return user
    return None


def issue_token(user: User) -> str:
    return create_access_token(user.id, user.role)
