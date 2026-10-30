# OncoScreen AI — Trợ lý hành trình tầm soát ung thư

Repo: https://github.com/Tuyen230605/OncoScreen-AI

> Hai AI agent dùng chung một lõi tri thức cho cả hành trình tầm soát tại bệnh viện:
> **Navigator** giúp người dân (chưa cần tài khoản) biết nên tầm soát loại ung thư nào, khi nào, bao lâu một lần — có nguồn —
> rồi mời tạo tài khoản và đặt lịch khi cần; **Clinical Copilot** tóm tắt hồ sơ xuyên suốt và soạn bản nháp kế hoạch để
> **bác sĩ sửa và duyệt (HITL)**. Chế độ mock chạy local không cần API key; chế độ agent thật gọi LLM từ nhà cung cấp được cấu hình.

⚠️ **AI KHÔNG chẩn đoán ung thư, KHÔNG diễn giải kết quả tầm soát.** Mọi khuyến nghị chỉ mang tính giáo dục / tham khảo và
phải qua bác sĩ duyệt. Chỉ dùng hồ sơ giả lập khi thử API LLM của bên thứ ba. Xem [docs/00_OVERVIEW.md](docs/00_OVERVIEW.md).

## Bắt đầu ở đâu?

| Bạn là… | Đọc theo thứ tự |
|---|---|
| Thành viên mới, muốn hiểu dự án | `docs/00_OVERVIEW.md` → `docs/02_BUSINESS_FLOW.md` → `docs/01_ARCHITECTURE.md` → `docs/05_AGENT_RELIABILITY.md` |
| Làm **AI Core** (Tuyền) | `docs/guides/GUIDE_AI_CORE.md` + `docs/protocols/AI_CORE_CONTRACT.md` |
| Làm **Backend** | `docs/guides/GUIDE_BACKEND.md` + `docs/protocols/API_CONTRACT.md` + `docs/protocols/DB_SCHEMA.md` |
| Làm **Frontend** | `docs/guides/GUIDE_FRONTEND.md` + `docs/protocols/API_CONTRACT.md` |
| Ghép nối / demo | `docs/guides/GUIDE_INTEGRATION.md` |
| Trước khi commit | `docs/protocols/GIT_WORKFLOW.md` + `docs/protocols/DEFINITION_OF_DONE.md` |

## Cấu trúc repo

```
.
├── ai_core/      # [Module 1] Navigator + Clinical Copilot (LangGraph), RAG lai, luật tầm soát, guardrails, eval
├── backend/      # [Module 2] FastAPI + PostgreSQL: tư vấn, đặt lịch, lần khám (HITL), hồ sơ xuyên suốt, scheduler
├── frontend/     # [Module 3] Next.js: Navigator công khai, cổng bệnh nhân, cổng bác sĩ
├── docs/         # Đặc tả, protocol, hướng dẫn từng khối, ADR
├── scripts/      # Script tiện ích chạy toàn hệ thống
├── topic/        # Đề bài gốc (không sửa)
└── docker-compose.yml  # PostgreSQL 16 cho dev/demo
```

## Chạy dự án local (Linux/macOS)

Cần Python 3.11+, Node.js/npm. Repo hiện có sẵn `ai_core/.venv` (Python 3.12.3), các thư viện backend/AI Core đã cài trong venv này, cùng `frontend/node_modules`. Docker Compose chỉ cần nếu dùng PostgreSQL. Các lệnh dưới đây chạy frontend + backend ở chế độ mock; backend gọi AI Core mock trực tiếp nên không cần bật server AI riêng.

### 1. Kích hoạt môi trường Python và cấu hình

Chạy từ thư mục gốc repo. Mỗi terminal mới cần kích hoạt venv lại:

```bash
source ai_core/.venv/bin/activate
```

Nếu cần cài lại/cập nhật dependencies sau khi thay đổi requirements:

```bash
source ai_core/.venv/bin/activate
python -m pip install -r requirements.txt
```

Repo hiện đã có `.env`. Nếu tạo checkout mới và chưa có file này, chạy `cp .env.example .env`. Giữ `USE_MOCK_AGENT=true` để backend gọi MockAgent. Frontend mặc định dùng API backend (`NEXT_PUBLIC_USE_MOCK_API=false`) tại localhost; luồng mock không cần `LLM_API_KEY`.

### 2. Chạy database

Mặc định `.env.example` dùng PostgreSQL. Khi dùng PostgreSQL phải đặt `SECRET_KEY` ngẫu nhiên ≥ 32 ký tự trong `.env` (backend từ chối khởi động nếu để trống/mặc định): `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Nếu máy đã cài Docker Engine và Docker Compose:

```bash
docker compose up -d db
```

Nếu chưa có Docker, có thể dùng SQLite cho dev: sửa dòng `DATABASE_URL` trong `.env` thành `DATABASE_URL=sqlite:///./dev.db`, rồi bỏ qua bước Docker. SQLite sẽ được backend khởi tạo tự động.

### 3. Chạy backend và tạo tài khoản demo

Mở terminal mới, chạy từ repo root:

```bash
source ai_core/.venv/bin/activate
cd backend
python scripts/seed.py
uvicorn app.main:app --reload --port 8000
```

Script seed tạo schema và tài khoản demo nếu chưa có. Mở Swagger tại <http://localhost:8000/docs>.

### 4. Chạy frontend

Mở terminal thứ hai:

```bash
cd frontend
npm ci                    # chỉ cần lần đầu hoặc khi package-lock.json thay đổi
npm run dev
```

Mở <http://localhost:3000>. Frontend mặc định gọi API ở `http://localhost:8000/api/v1`; không cần tạo `.env` riêng cho frontend khi chạy local theo cấu hình mặc định.

### 5. Tài khoản demo

Mật khẩu chung: `123456`.

| Vai trò | Email |
|---|---|
| Bác sĩ | `doctor@demo.vn` |
| Bệnh nhân | `lan@demo.vn` |
| Bệnh nhân | `hung@demo.vn` (có sẵn một lịch hẹn tầm soát phổi để bác sĩ demo Copilot) |

### Chạy riêng AI Core mock (tùy chọn)

Để xem JSON demo của AI Core mà không qua giao diện/API, chạy từ repo root trong terminal đã kích hoạt venv:

```bash
source ai_core/.venv/bin/activate
cd ai_core
python -m ai_core.cli demo
```

Có thể thay case bằng `python -m ai_core.cli demo --case lung` hoặc `python -m ai_core.cli demo --case red-flag`. Đây là lệnh demo độc lập; khi chạy full-stack, backend gọi MockAgent trực tiếp.

`requirements.txt` cài dependencies cho Backend, AI Core, local embedding và OpenRouter/OpenAI provider. Để dùng agent thật: đặt `USE_MOCK_AGENT=false` và `LLM_API_KEY` trong `.env`, chạy `cd ai_core && python scripts/ingest.py` để nạp guideline vào vector store (không bắt buộc — thiếu vector store thì RAG tự dùng BM25), rồi khởi động lại backend; `http://localhost:8000/api/v1/health` báo `agent: "real"`. Chỉ dùng hồ sơ giả khi gọi LLM bên thứ ba.

### Thử hành trình (demo)

1. Mở <http://localhost:3000> (chưa đăng nhập), hỏi Navigator: *"Tôi là nữ 45 tuổi, mẹ tôi bị ung thư vú, nên tầm soát gì?"* → gợi ý có nguồn + nút tạo tài khoản để đặt lịch.
2. Tạo tài khoản (phiên tư vấn được gắn, hồ sơ điền sẵn) → đặt lịch.
3. Đăng nhập `doctor@demo.vn` → hàng chờ → xác nhận → **Bắt đầu khám** → xem brief của Copilot, hỏi Copilot, điền ngày hẹn cho kế hoạch, viết kết luận, duyệt.
4. Quay lại tài khoản bệnh nhân → hồ sơ xuyên suốt, kết luận, kế hoạch, nhắc lịch, hỏi đáp về kế hoạch.
5. Thử red-flag: *"Em sờ thấy một khối cứng ở vú"* → ngắt tư vấn, khuyên khám sớm, lịch ưu tiên.

Đánh giá agent: `cd ai_core && python -m ai_core.cli eval` (golden set 40 ca; thêm `--real` để đo với LLM). Các kỹ thuật tăng độ tin cậy (RAG lai, guardrail, HITL, tracing, metrics): [docs/05_AGENT_RELIABILITY.md](docs/05_AGENT_RELIABILITY.md). Tài liệu sơ lược dự án dạng Word: `docs/report/`.

## Nguyên tắc làm việc (bắt buộc)

1. **Chỉ sửa trong thư mục khối của mình.** Muốn đổi contract (`docs/protocols/*`, `ai_core/ai_core/schemas.py`,
   `frontend/src/types/api.ts`) → mở PR riêng, tag cả team. Xem `docs/protocols/OWNERSHIP.md`.
2. **Mock trước, thật sau.** Mỗi khối có mock của khối kế bên để không phải chờ nhau.
3. **Nhánh `feature/<tên>-<việc>`, commit nhỏ, PR trước khi merge.** Xem `docs/protocols/GIT_WORKFLOW.md`.
