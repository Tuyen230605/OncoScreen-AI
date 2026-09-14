# Guide: Module 1 — AI Core & Data (Tuyền)

**Bạn sở hữu:** `ai_core/`. **Bạn cung cấp cho backend:** package `ai_core` với interface trong `AI_CORE_CONTRACT.md`.
**Bạn không cần chờ ai.** Backend/Frontend dùng `MockAgent` của bạn trong lúc bạn làm phần thật.

## 0. Chạy lần đầu
```bash
cd ai_core
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash; PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest -q                      # phải pass ngay với khung (test schema + mock)
python -m ai_core.cli demo     # chạy MockAgent với 1 ca mẫu, in JSON
```

## 1. Việc cần làm (theo thứ tự ưu tiên)

### 1.1 Chốt contract & mock (M1) — làm TRƯỚC, để BE/FE có cái mà dùng
- [ ] Rà `ai_core/schemas.py`: đủ trường chưa? Thiếu gì thêm ngay ở M1 (sau M1 sửa contract phải PR `contract/*`).
- [ ] `data/questionnaire.json`: bộ câu hỏi động. Mỗi câu có `id`, `text`, `type`, `options`, `depends_on` (câu hỏi con hiện khi câu cha có giá trị nhất định, vd. `pack_years` chỉ hỏi nếu `smoking=true`).
- [ ] `data/red_flags.json`: danh sách triệu chứng nguy hiểm + severity + lời khuyên. Câu hỏi triệu chứng trong questionnaire có `id` khớp mã red-flag.
- [ ] `mock.py`: `MockAgent` trả kết quả hợp lệ cho 3 kịch bản demo (xem `02_BUSINESS_FLOW.md`). Mock **phải** bắt red-flag thật (rule-based) để FE test được màn cảnh báo.

### 1.2 Dữ liệu guideline & RAG (M2)
- [ ] Thu thập guideline tầm soát (ưu tiên nguồn mở: USPSTF, ACS, WHO, Bộ Y tế VN, hướng dẫn bệnh viện K…). Lưu `data/guidelines/<cancer_type>_<source>.md` với **frontmatter** metadata:
  ```yaml
  ---
  cancer_type: breast
  source: "USPSTF 2024"
  url: https://...
  gender: female        # male | female | any
  min_age: 40
  max_age: 74
  risk_level: average   # average | elevated | high | any
  ---
  ```
- [ ] `rag/ingest.py`: đọc md → chunk (theo heading, ~500 token) → embed → lưu Chroma tại `VECTOR_STORE_DIR`, metadata giữ nguyên frontmatter.
- [ ] `rag/retriever.py`: `retrieve(profile, risk_factors, k=6)` — lọc metadata (gender, tuổi trong khoảng) **trước** rồi mới similarity search. Trả `list[Source]`.
- [ ] `scripts/ingest.py`: CLI chạy ingest, có `--reset`.

### 1.3 LangGraph (M2)
State: `graph/state.py::AgentState` (TypedDict). Nodes trong `graph/nodes/`:

| Node | Input → Output | Ghi chú |
|---|---|---|
| `collect` | profile + answers → `missing_questions` | Quyết định còn thiếu câu nào (rule-based, không cần LLM) |
| `red_flag` | answers → `RedFlagResult` | **Rule-based**, chạy trước mọi thứ. Nếu detected → END |
| `assess_risk` | profile + answers → `RiskAssessment` | LLM + rule; output structured (Pydantic) |
| `retrieve` | risk → `sources` | RAG |
| `recommend` | sources + risk → `ScreeningPlan` | LLM, **bắt buộc** trích `sources` cho từng item; structured output |
| `guardrail` | plan → plan (validated) | `guardrails/safety.py`: chặn từ ngữ chẩn đoán, chặn item không source, thêm disclaimer |

Edges: `collect → red_flag → (detected? END : assess_risk) → retrieve → recommend → guardrail → END`.
`graph/build.py::build_graph()` trả compiled graph; `api.py::ScreeningAgent.run_screening` gọi `graph.invoke(state)`.

### 1.4 Tools (tên theo đề bài)
`tools/questionnaire.py`, `tools/red_flag_detector.py`, `tools/screening_recommender.py`, `tools/booking.py` (mô phỏng: tính `next_due` từ `interval_months`), `tools/recall_reminder.py` (tính lịch nhắc tiếp theo sau khi hoàn thành). Node gọi tool; tool thuần Python, test được không cần LLM.

### 1.5 Guardrails & prompt
- Tất cả prompt ở `prompts.py`. System prompt phải có: vai trò "trợ lý giáo dục tầm soát", **cấm chẩn đoán**, cấm diễn giải kết quả xét nghiệm, chỉ dùng thông tin trong `sources`, tiếng Việt, giọng bình tĩnh.
- `guardrails/safety.py::validate_plan(plan)`: raise `GuardrailViolation` nếu vi phạm; `recommend` retry 1 lần rồi fail rõ ràng.
- `guardrails/disclaimer.py::DISCLAIMER_VI`: chuỗi chuẩn, backend/FE dùng lại.

### 1.6 Nâng cao (M3)
- Education content theo cancer_type (`get_education`) — có thể lấy từ chính guideline md.
- Memory: `PatientContext.prior_sessions_summary` — backend truyền tóm tắt phiên trước, bạn đưa vào prompt.
- Eval nhỏ: `tests/eval_cases.json` 10 ca → kiểm tra plan có đúng loại tầm soát kỳ vọng.

## 2. Cấu hình LLM
`llm.py::get_chat_model()` đọc `LLM_PROVIDER`:
- `anthropic` (mặc định, `langchain-anthropic`, model `claude-opus-5`)
- `openai` (`langchain-openai`) · `ollama` (`langchain-ollama`, chạy offline, vd. `qwen2.5:7b`)
Embedding: `EMBEDDING_PROVIDER=local` dùng `sentence-transformers` đa ngôn ngữ (offline, khuyến nghị cho tiếng Việt).

## 3. Định nghĩa "xong" cho khối bạn
Xem `DEFINITION_OF_DONE.md` mục AI Core. Ngoài ra: `USE_MOCK_AGENT=false` + `python -m ai_core.cli demo --real` chạy ra plan có source thật.

## 4. Đừng làm
- Đừng trả kết quả trực tiếp cho người dùng (đó là việc backend/HITL).
- Đừng import gì từ `backend/`. AI Core phải chạy độc lập.
- Đừng để LLM tự quyết định red-flag — dùng rule trước, LLM chỉ bổ sung (nếu có) và **không được** hạ cấp cảnh báo.
