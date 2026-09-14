# backend — Module 2: FastAPI + PostgreSQL + HITL + Scheduler

Hướng dẫn chi tiết: [docs/guides/GUIDE_BACKEND.md](../docs/guides/GUIDE_BACKEND.md).
Contract: [API_CONTRACT.md](../docs/protocols/API_CONTRACT.md) · [DB_SCHEMA.md](../docs/protocols/DB_SCHEMA.md) · [AI_CORE_CONTRACT.md](../docs/protocols/AI_CORE_CONTRACT.md).

```bash
pip install -r requirements.txt && pip install -e ../ai_core
uvicorn app.main:app --reload      # http://localhost:8000/docs
pytest -q
```

Cấu trúc: `app/api/v1/*` (router mỏng) → `app/services/*` (logic) → `app/models/*` (ORM). Schemas response ở `app/schemas/*`.
