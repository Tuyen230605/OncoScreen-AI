"""FastAPI app factory. Chạy: uvicorn app.main:app --reload"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.database import init_db
from app.services import scheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.is_sqlite:
        init_db()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="OncoScreen AI API",
    version="0.1.0",
    description="API cho hệ thống AI Agent hỗ trợ tầm soát ung thư (HITL). Xem docs/protocols/API_CONTRACT.md",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")
