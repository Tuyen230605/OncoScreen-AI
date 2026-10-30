"""Settings backend — đọc .env ở root repo."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SECRET_KEY = "change-me-in-dev"
MIN_SECRET_KEY_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./dev.db"
    secret_key: str = DEFAULT_SECRET_KEY
    access_token_expire_minutes: int = 480
    cors_origins: str = "http://localhost:3000"
    use_mock_agent: bool = True
    reminder_tick_seconds: int = 60

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    def check_secret_key(self) -> None:
        """Ngoài SQLite (dev/test), từ chối khởi động với SECRET_KEY mặc định/ngắn: ai biết key là giả mạo được JWT."""
        if self.is_sqlite:
            return
        if self.secret_key == DEFAULT_SECRET_KEY or len(self.secret_key) < MIN_SECRET_KEY_LENGTH:
            raise RuntimeError(
                f"SECRET_KEY mặc định hoặc ngắn hơn {MIN_SECRET_KEY_LENGTH} ký tự — đặt chuỗi ngẫu nhiên, vd. "
                '`python -c "import secrets; print(secrets.token_urlsafe(48))"`'
            )


settings = Settings()
