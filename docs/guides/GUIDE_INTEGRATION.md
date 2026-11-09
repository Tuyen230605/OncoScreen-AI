# Guide: Tích hợp FE, BE và AI Core

AI Core là package Python được backend gọi trực tiếp, không có server/port riêng. Frontend gọi REST API của backend. `USE_MOCK_AGENT=true` chạy cùng pipeline (luật, red-flag, BM25, guardrail) nhưng không gọi LLM; `false` bật LLM. LLM lỗi hoặc bị guardrail chặn → agent tự trả câu trả lời mẫu xác định (trace ghi `template_fallback`).

## Khởi động (từ root repo; venv ở `.venv/` gốc repo — lệnh Windows xem `README.md` §"Chạy dự án local")

```bash
# Terminal 1: tạo venv nếu chưa có, rồi kích hoạt (Git Bash trên Windows: .venv/Scripts/activate)
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
[ -f .env ] || cp .env.example .env

# Chọn database: với PostgreSQL cần Docker
docker compose up -d db
# Nếu không có Docker: đặt DATABASE_URL=sqlite:///./dev.db trong .env; bỏ qua lệnh docker.

cd backend
python scripts/seed.py
uvicorn app.main:app --reload --port 8000
```

```bash
# Terminal 2
cd frontend
npm ci
npm run dev
```

Mở `http://localhost:3000`, API docs `http://localhost:8000/docs`. Frontend dùng backend thật khi `NEXT_PUBLIC_USE_MOCK_API=false` (mặc định). Nếu mở terminal mới cho Python, kích hoạt lại cùng venv. Không cần khởi động AI Core riêng.

## Bật agent thật và ingest mẫu

1. Đặt `USE_MOCK_AGENT=false` trong `.env` ở root. Với key OpenRouter: `LLM_PROVIDER=openrouter`, `LLM_API_KEY` là key OpenRouter. Để demo bằng hồ sơ giả mà không cần credit, đặt `LLM_MODEL=nvidia/nemotron-3-super-120b-a12b:free`. Khi dùng dữ liệu bệnh nhân thật, cần chọn model và chính sách xử lý dữ liệu phù hợp; không dùng endpoint miễn phí này. Các provider khác cần model và key đúng nhà cung cấp. Không commit `.env`.

   [OpenRouter hướng dẫn endpoint tương thích OpenAI](https://openrouter.ai/docs/community/frameworks) và [thông tin model miễn phí](https://openrouter.ai/nvidia/nemotron-3-super-120b-a12b%3Afree) là căn cứ cho cấu hình demo. Key OpenRouter thông thường bắt đầu bằng `sk-or-`; nếu nhận lỗi xác thực, kiểm tra lại key trong tài khoản OpenRouter, không gửi key qua chat hoặc commit.
2. Chạy ingest khi muốn có RAG từ file `ai_core/data/guidelines/*.md`:

   ```bash
   # từ root repo, sau khi kích hoạt venv và cài requirements.txt
   cd ai_core
   python scripts/ingest.py
   ```

3. Khởi động lại backend và xem `GET /api/v1/health` trả `agent:"real"`.

`requirements.txt` bao gồm local embedding. Lần đầu tải model có thể cần mạng. Nếu chưa ingest hoặc không có nguồn hợp với tuổi/giới/nguy cơ, RAG trả rỗng; phiên vẫn sang hàng chờ bác sĩ, không tự tạo kế hoạch. Nếu LLM provider lỗi, agent cũng trả trạng thái thiếu căn cứ. Xem log backend theo `trace_id` và `GET /doctor/metrics` để quan sát.

## Tài khoản demo và luồng kiểm tra

`python backend/scripts/seed.py` tạo tài khoản sau (mật khẩu chung `123456`) và một lịch hẹn tầm soát phổi cho `hung@demo.vn`:

| Vai trò | Email |
|---|---|
| Bác sĩ | `doctor@demo.vn` |
| Bệnh nhân | `lan@demo.vn` |
| Bệnh nhân | `hung@demo.vn` |

1. **Navigator ẩn danh**: mở `http://localhost:3000` khi chưa đăng nhập, hỏi "Tôi là nữ 45 tuổi, mẹ tôi bị ung thư vú, nên tầm soát gì?" hoặc làm bảng hỏi nhanh. Thấy gợi ý có nguồn và nút tạo tài khoản.
2. **Red-flag**: ở phiên mới, nhập "Em sờ thấy một khối cứng ở vú" → cảnh báo khám sớm, không có gợi ý tầm soát, CTA đặt lịch ưu tiên.
3. **Ngoài phạm vi**: "Kết quả PSA của tôi là 6 có phải ung thư không?" → từ chối chẩn đoán, mời đặt lịch.
4. **Tạo tài khoản & đặt lịch**: từ CTA, đăng ký → hồ sơ điền sẵn → đặt lịch (dịch vụ chọn sẵn).
5. **Bác sĩ**: đăng nhập `doctor@demo.vn` → hàng chờ (khẩn lên đầu) → xác nhận → **Bắt đầu khám** → brief của Copilot (dữ kiện trỏ về mốc hồ sơ, gợi ý guideline, câu hỏi cần làm rõ, khoảng trống dữ liệu) → hỏi Copilot → sửa bản nháp, điền ngày hẹn → viết kết luận → duyệt.
6. **Theo dõi**: đăng nhập lại bệnh nhân → hồ sơ xuyên suốt, kết luận, kế hoạch, nhắc lịch; hỏi đáp về kế hoạch đã duyệt; đánh dấu đã tầm soát → chu kỳ kế tiếp.
7. **Quan sát AI**: dashboard bác sĩ hiển thị `GET /doctor/metrics` và danh sách trace `GET /doctor/agent-runs`.

Tài khoản bác sĩ chỉ được tạo qua seed/quản trị viên. `agent_runs` lưu metadata từng node (thời lượng, số nguồn, bộ sinh văn bản, kết quả guard), không lưu nội dung hội thoại.

## Sự cố thường gặp

| Triệu chứng | Cách kiểm tra |
|---|---|
| `docker: command not found` | Dùng SQLite dev bằng `DATABASE_URL=sqlite:///./dev.db`, hoặc cài Docker/Compose. |
| Không có `python`/`uvicorn` | Kích hoạt đúng venv và chạy `python -m pip install -r requirements.txt`. |
| `/api/v1/health` vẫn báo `mock` | Kiểm tra `USE_MOCK_AGENT=false` trong root `.env`, khởi động lại backend. |
| Trace ghi `generator=template_fallback`, `guard=llm_error` | LLM lỗi (key, quota, model). Kiểm tra log `navigator_llm_unavailable`; với OpenRouter có thể chuyển sang model miễn phí để demo bằng hồ sơ giả. |
| Trace `retrieve` báo `mode=lexical`, `dense=unavailable` | Chưa ingest vector store hoặc thiếu model embedding; RAG vẫn chạy bằng BM25. Chạy `python scripts/ingest.py` trong `ai_core/`. |
| Brief không có `draft_plan` | Hồ sơ có red-flag (cố ý), hoặc chưa đủ tuổi/giới, hoặc không có luật tầm soát áp dụng. |
| FE lỗi CORS | Kiểm tra `CORS_ORIGINS` trong `.env` chứa `http://localhost:3000`. |
