"""CLI phải in được tiếng Việt kể cả khi console không phải UTF-8 (Windows cp1252)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

AI_CORE_DIR = Path(__file__).resolve().parents[1]


def _run_cli(*args: str) -> subprocess.CompletedProcess[bytes]:
    env = {**os.environ, "PYTHONIOENCODING": "cp1252", "LLM_API_KEY": "", "USE_MOCK_AGENT": "true"}
    env.pop("PYTHONUTF8", None)
    return subprocess.run(
        [sys.executable, "-m", "ai_core.cli", *args],
        cwd=AI_CORE_DIR,
        env=env,
        capture_output=True,
        timeout=120,
        check=False,
    )


def test_demo_prints_vietnamese_on_non_utf8_console() -> None:
    proc = _run_cli("demo", "--case", "breast")
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    out = proc.stdout.decode("utf-8")
    assert "=== Navigator ===" in out
    assert "tầm soát" in out


def test_eval_runs_on_non_utf8_console() -> None:
    proc = _run_cli("eval")
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    assert proc.stdout.decode("utf-8").strip()
