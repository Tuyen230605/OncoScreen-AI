from __future__ import annotations

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._common import Timestamps, UUIDPk


class AuditLog(UUIDPk, Timestamps, Base):
    __tablename__ = "audit_logs"

    session_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("screening_sessions.id"), nullable=True)
    actor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
