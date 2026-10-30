import pytest
from fastapi.testclient import TestClient

from app.config import DEFAULT_SECRET_KEY, Settings, settings
from app.main import app

POSTGRES = "postgresql+psycopg://postgres:postgres@localhost:5432/oncoscreen"
STRONG = "s" * 48


@pytest.mark.parametrize("secret", [DEFAULT_SECRET_KEY, "short-secret"])
def test_non_sqlite_refuses_default_or_short_secret(secret):
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        Settings(database_url=POSTGRES, secret_key=secret).check_secret_key()


def test_strong_secret_or_sqlite_is_accepted():
    Settings(database_url=POSTGRES, secret_key=STRONG).check_secret_key()
    Settings(database_url="sqlite:///./dev.db", secret_key=DEFAULT_SECRET_KEY).check_secret_key()


def test_app_does_not_start_with_default_secret_on_postgres(monkeypatch):
    monkeypatch.setattr(settings, "database_url", POSTGRES)
    monkeypatch.setattr(settings, "secret_key", DEFAULT_SECRET_KEY)
    with pytest.raises(RuntimeError, match="SECRET_KEY"), TestClient(app):
        pass
