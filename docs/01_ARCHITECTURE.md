# 01 — Kiến trúc hệ thống

## Sơ đồ khối

```
┌──────────────────────────── Frontend (Next.js :3000) ────────────────────────────┐
│  /login   /patient/*  (khảo sát, kết quả, nhắc lịch)   /doctor/*  (dashboard duyệt) │
└───────────────────────────────────────┬──────────────────────────────────────────┘
                                        │ REST JSON  (docs/protocols/API_CONTRACT.md)
┌───────────────────────────────────────▼──────────────────────────────────────────┐
│                         Backend (FastAPI :8000)  /api/v1                          │
│  api/v1: auth · patients · sessions · doctor(HITL) · reminders · education        │
│  services: agent_service ─┐  hitl_service   scheduler(APScheduler)   auth_service │
│  models (SQLAlchemy) ─────┼──────────────► PostgreSQL / SQLite                    │
└───────────────────────────┼──────────────────────────────────────────────────────┘
                            │ Python call  (docs/protocols/AI_CORE_CONTRACT.md)
┌───────────────────────────▼──────────────────────────────────────────────────────┐
│                     AI Core (Python package `ai_core`)                            │
│  api.py: get_questionnaire · check_red_flags · run_screening · get_education      │
│  graph/ (LangGraph): collect → red_flag → retrieve → recommend → draft            │
│  tools/: questionnaire · red_flag_detector · screening_recommender · booking …    │
│  rag/: ingest → Chroma (data/vector_store) ← data/guidelines/*.md                 │
│  guardrails/: safety (no-diagnosis) · disclaimer                                  │
│  llm.py: factory theo LLM_PROVIDER                                                │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Cách các khối giao tiếp (ranh giới cố định)

| Ranh giới | Cơ chế | Ai sở hữu định nghĩa | File nguồn sự thật |
|---|---|---|---|
| Frontend ↔ Backend | HTTP REST JSON + JWT Bearer | Backend | `docs/protocols/API_CONTRACT.md`, mirror TS: `frontend/src/types/api.ts` |
| Backend ↔ AI Core | Gọi hàm Python trực tiếp (import package) | AI Core | `docs/protocols/AI_CORE_CONTRACT.md`, `ai_core/ai_core/schemas.py` |
| AI Core ↔ Vector DB | Chroma client (file-based) | AI Core | `ai_core/ai_core/rag/` |
| Backend ↔ DB | SQLAlchemy ORM | Backend | `docs/protocols/DB_SCHEMA.md`, `backend/app/models/` |

**Tại sao Backend gọi AI Core bằng import chứ không HTTP?** Chạy local, 1 process là đủ, ít lỗi ghép nối, dễ debug.
Nếu sau này cần tách service, chỉ cần bọc `ai_core/api.py` bằng FastAPI riêng — contract không đổi (xem ADR-0002).

## Chiến lược làm song song (mock)
```
Frontend  ──► NEXT_PUBLIC_USE_MOCK_API=true ──► src/mocks/fixtures.ts   (không cần backend)
Backend   ──► USE_MOCK_AGENT=true           ──► ai_core.mock.MockAgent   (không cần LLM/RAG)
AI Core   ──► pytest + script CLI            ──► không cần backend/frontend
```
Khi mỗi khối xong, tắt flag mock để ghép thật. Xem `docs/guides/GUIDE_INTEGRATION.md`.

## Trạng thái phiên tầm soát (state machine — dùng chung cho cả 3 khối)

```
            answers còn thiếu
  ┌─────────────────────┐
  ▼                     │
collecting ──────────────┘
  │ đủ câu trả lời
  ├── red-flag phát hiện ──► red_flag        (ngắt; hiển thị cảnh báo đi khám; KHÔNG có plan)
  │
  └── không red-flag ──► agent chạy RAG ──► pending_review   (draft_plan; patient chưa thấy)
                                                │
                                   bác sĩ duyệt │
                             ┌──────────────────┼──────────────────┐
                             ▼                                     ▼
                         approved  (final_plan; sinh reminders)  rejected (note cho patient)
                             │
                 patient đánh dấu hoàn thành mốc
                             ▼
                         completed (tuỳ chọn, nâng cao)
```

Enum chuẩn: `collecting | red_flag | pending_review | approved | rejected | completed`
(định nghĩa tại `ai_core/ai_core/schemas.py::SessionStatus` và `frontend/src/types/api.ts`).

## Thư mục chi tiết

```
ai_core/
├── ai_core/
│   ├── api.py            # ★ Entry point duy nhất backend được gọi (ScreeningAgent + MockAgent)
│   ├── schemas.py        # ★ Contract Pydantic (KHÔNG sửa tuỳ tiện)
│   ├── config.py         # đọc env
│   ├── llm.py            # factory LLM theo provider
│   ├── mock.py           # MockAgent: dữ liệu giả hợp lệ theo contract
│   ├── graph/            # LangGraph: state.py, build.py, nodes/*
│   ├── tools/            # questionnaire, red_flag_detector, screening_recommender, booking, recall_reminder
│   ├── rag/              # embeddings.py, ingest.py, retriever.py
│   └── guardrails/       # safety.py (no-diagnosis), disclaimer.py
├── data/
│   ├── guidelines/*.md   # tài liệu guideline (nguồn RAG) — có frontmatter metadata
│   ├── questionnaire.json
│   ├── red_flags.json
│   └── vector_store/     # Chroma sinh ra (gitignore)
├── scripts/ingest.py
└── tests/

backend/
├── app/
│   ├── main.py           # tạo FastAPI app, mount router, CORS, startup scheduler
│   ├── config.py         # Settings (pydantic-settings)
│   ├── database.py       # engine, SessionLocal, Base
│   ├── models/           # SQLAlchemy: user, patient_profile, screening_session, reminder, audit_log
│   ├── schemas/          # Pydantic request/response (mirror API_CONTRACT)
│   ├── api/
│   │   ├── deps.py       # get_db, get_current_user, require_role
│   │   └── v1/           # auth, patients, sessions, doctor, reminders, education, router
│   ├── services/         # agent_service (bridge → ai_core), hitl_service, scheduler, auth_service
│   └── core/security.py  # hash, JWT
├── alembic/              # migrations
└── tests/

frontend/
├── src/
│   ├── app/
│   │   ├── login/
│   │   ├── patient/      # survey, results/[id], reminders
│   │   └── doctor/       # dashboard (page.tsx), sessions/[id]
│   ├── components/       # Disclaimer, RedFlagAlert, PlanTable, QuestionForm, ...
│   ├── lib/api.ts        # client HTTP duy nhất (switch mock)
│   ├── types/api.ts      # ★ mirror API_CONTRACT (KHÔNG sửa tuỳ tiện)
│   └── mocks/fixtures.ts
└── public/
```
