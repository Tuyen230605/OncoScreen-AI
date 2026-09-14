"""Cấu hình AI Core — đọc từ .env ở root repo (hoặc env hệ thống)."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_DIR = Path(__file__).resolve().parent
AI_CORE_DIR = PACKAGE_DIR.parent
REPO_ROOT = AI_CORE_DIR.parent
DATA_DIR = AI_CORE_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: str = "anthropic"  # anthropic | openai | ollama
    llm_model: str = "claude-opus-5"
    llm_api_key: str | None = None

    embedding_provider: str = "local"  # local | openai
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    vector_store_dir: Path = DATA_DIR / "vector_store"

    use_mock_agent: bool = True


settings = Settings()
