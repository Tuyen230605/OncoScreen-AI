from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DB
from app.services.agent_service import agent_name

router = APIRouter()


@router.get("/health")
def health(db: DB) -> dict:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "agent": agent_name(), "db": "ok"}
