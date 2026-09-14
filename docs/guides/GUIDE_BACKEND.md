# Guide: Module 2 — Backend & Database

**Bạn sở hữu:** `backend/`. **Bạn cung cấp:** REST API theo `API_CONTRACT.md`. **Bạn tiêu thụ:** `ai_core` theo `AI_CORE_CONTRACT.md`.
**Không cần chờ AI Core:** đặt `USE_MOCK_AGENT=true`.

## 0. Chạy lần đầu
```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements.txt
pip install -e ../ai_core            # để import được package ai_core
cp ../.env.example ../.env           # DATABASE_URL mặc định trỏ tới Postgres của docker compose
(cd .. && docker compose up -d)      # PostgreSQL 16; hoặc SQLite: DATABASE_URL=sqlite:///./dev.db
uvicorn app.main:app --reload        # http://localhost:8000/docs
pytest -q
```

## 1. Việc cần làm

### 1.1 Nền (M0–M1)
- [ ] `config.py`: `Settings` (pydantic-settings) đọc `.env` ở root repo.
- [ ] `database.py`: engine từ `DATABASE_URL`; nếu sqlite → `create_all` lúc startup; Postgres → Alembic (`alembic upgrade head` sau khi `docker compose up -d`).
- [ ] `models/`: 5 bảng theo `DB_SCHEMA.md`. `alembic init` + migration đầu tiên.
- [ ] `core/security.py`: `bcrypt`, JWT (`python-jose`), `create_access_token`.
- [ ] `api/deps.py`: `get_db`, `get_current_user`, `require_role("doctor")`.
- [ ] `api/v1/auth.py`: register / login / me.

### 1.2 Luồng session (M1)
- [ ] `api/v1/patients.py`: GET/PUT profile.
- [ ] `services/agent_service.py`: bọc `ai_core.api.get_agent()`; gọi trong `run_in_threadpool`; map `AgentError` → 502.
- [ ] `api/v1/sessions.py`:
  - `POST /sessions`: tạo session `collecting`, gọi `get_questionnaire(profile)`, lưu snapshot.
  - `POST /sessions/{id}/answers`: merge answers → `check_red_flags` → nếu detected: `red_flag`, lưu, trả. Nếu chưa đủ câu (`collect` báo thiếu) → giữ `collecting`. Đủ → `run_screening` → `pending_review`, lưu `draft_plan`, `risk_assessment`, `trace_id`.
  - `GET /sessions/{id}`: **áp dụng quy tắc lộ dữ liệu** (serializer khác nhau theo role) — viết test.
- [ ] `schemas/`: Pydantic response khớp API_CONTRACT. Với `ScreeningPlan` v.v. **import thẳng từ `ai_core.schemas`**, đừng định nghĩa lại.

### 1.3 HITL (M1–M2)
- [ ] `api/v1/doctor.py` + `services/hitl_service.py`: list pending, review approve/reject, gán `doctor_id`, `reviewed_at`, ghi `audit_logs` (diff `draft_plan` vs `final_plan`).
- [ ] Approve → `services/scheduler.py::create_reminders_for_plan(session)` sinh reminders từ `final_plan.items[].next_due`.

### 1.4 Scheduler (M2)
- [ ] APScheduler `BackgroundScheduler` khởi động trong lifespan của FastAPI; job mỗi `REMINDER_TICK_SECONDS`: reminders `scheduled` có `due_date <= today` → `due` + `message` (dùng `ai_core.tools.recall_reminder` hoặc template).
- [ ] `POST /reminders/{id}/complete` → `done`; (nâng cao) tạo reminder kế tiếp theo `interval_months`.

### 1.5 Khác
- [ ] `api/v1/education.py`: proxy `agent.get_education`.
- [ ] `GET /health`.
- [ ] `scripts/seed.py`: tạo 1 doctor + 2 patient demo (`doctor@demo.vn / 123456`, …) để FE và demo dùng.
- [ ] CORS cho `CORS_ORIGINS`.

## 2. Test tối thiểu (`backend/tests/`)
- `test_auth.py`: register/login/me; sai mật khẩu → 401.
- `test_sessions_flow.py` (với MockAgent): tạo session → trả lời bình thường → `pending_review`; trả lời có red-flag → `red_flag`.
- `test_visibility.py`: patient không thấy `draft_plan`; patient B 403/404 với session của A; doctor thấy đủ.
- `test_hitl.py`: approve → `approved` + reminders được tạo; review khi status sai → 409.

Dùng SQLite in-memory + `TestClient`; fixture trong `conftest.py`.

## 3. Đừng làm
- Đừng import `ai_core.graph/*`, `ai_core.rag/*` — chỉ `ai_core.api` và `ai_core.schemas`.
- Đừng nhét logic vào router. Router → service.
- Đừng trả `draft_plan` cho patient dù chỉ để "tiện debug".
