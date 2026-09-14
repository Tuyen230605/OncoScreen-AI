"""Engine + session factory. SQLite → create_all lúc startup; Postgres → Alembic."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.is_sqlite else {}
engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Chỉ dùng cho SQLite/dev/test. Postgres dùng `alembic upgrade head`."""
    import app.models  # noqa: F401 — đăng ký models

    Base.metadata.create_all(bind=engine)
