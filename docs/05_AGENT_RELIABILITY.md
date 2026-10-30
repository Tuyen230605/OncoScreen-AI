# 05 — Độ tin cậy của Agent

Nguyên tắc thiết kế: **"Luật trước, LLM sau — mọi thứ LLM nói phải truy vết được, mọi lỗi phải rơi về trạng thái an toàn."**
Tài liệu này mô tả các lớp kỹ thuật đang chạy trong code (không phải kế hoạch), kèm vị trí file.

```
                ┌──────────── Input guard ────────────┐  ┌──── Xử lý ─────┐  ┌──────── Output guard ────────┐
Tin nhắn ──►  out-of-scope · injection · RED-FLAG ──►  luật tầm soát + RAG ──►  LLM ──►  chẩn đoán? trích dẫn? con số? ──► HITL ──► Người dùng
                     (luật, không LLM)                 (xác định, có nguồn)         (vi phạm → mẫu xác định)        (bác sĩ duyệt)
                └────────────────────── Tracing từng node → agent_runs → metrics / eval ──────────────────────────────┘
```

## 1. Kiến trúc agent: LangGraph có nhánh an toàn tường minh

| Agent | Graph | File |
|---|---|---|
| Navigator | `input_guard → update_intake ─(red-flag)→ triage` / `→ eligibility → [retrieve] → respond → triage` | `ai_core/agents/navigator.py` |
| Clinical Copilot | `load_record → eligibility → retrieve → draft_brief → draft_plan` | `ai_core/agents/copilot.py` |

- Red-flag **ngắt trước** mọi bước RAG/LLM (test xác nhận node `retrieve`/`respond` không chạy).
- Hai agent dùng chung tool (`tools/`), RAG (`rag/`), guardrail (`guardrails/`), tracing (`observability.py`) nhưng **khác prompt, khác quyền và khác chính sách**: Navigator nói với người dân → chỉ gợi ý theo nhóm; Copilot nói với bác sĩ → được đọc toàn bộ hồ sơ nhưng mọi dữ kiện phải trỏ về `event_id`.
- `MockAgent` = cùng pipeline, tắt LLM và vector store → hành vi an toàn của mock trùng agent thật; FE/BE/CI chạy không cần API key.

## 2. Rules-first: quyết định y khoa không giao cho LLM
- **Eligibility engine** (`tools/eligibility.py`, `data/screening_rules.json`): mỗi luật = giới, khoảng tuổi, điều kiện (`pack_years>=20`, `cirrhosis`, `hepatitis_without_cirrhosis` — viêm gan B/C chưa xơ gan chỉ gợi ý trao đổi với bác sĩ, không đặt chu kỳ, đúng mục "Đối tượng" của AASLD 2023), phương pháp, tuổi bắt đầu, chu kỳ và **trỏ tới một mục guideline cụ thể** (`doc_id` + `section`). Luật trỏ sai tài liệu → lỗi ngay khi load (fail fast); test kiểm tra mọi luật.
- LLM chỉ **diễn giải** gợi ý đã tính sẵn; prompt cấm thêm/bớt mục, đổi con số.
- Trích xuất thông tin (`tools/intake.py`): luật tiếng Việt (có dấu/không dấu, phủ định, phân biệt "tôi bị" với "mẹ tôi bị", tuổi của người thân); LLM chỉ **điền chỗ trống**, không ghi đè giá trị luật đã xác định.

## 3. RAG

### 3.1 Dữ liệu
- Nguồn: guideline chính thức (USPSTF, WHO, AASLD…), biên tập thành Markdown có frontmatter: `cancer_type, source, url, gender, min_age, max_age, risk_level, language, jurisdiction, publication_date, review_status`. Thiếu metadata bắt buộc → ingest từ chối.
- Quy trình `raw_data/` (bản gốc + `source.yaml` xuất xứ, giấy phép) → bản tóm tắt đã kiểm tra → `guidelines/*.md` → ingest. Không lưu PHI trong kho tri thức.
- Hiện có 8 tài liệu: vú (USPSTF 2024), cổ tử cung (USPSTF 2018, WHO 2021), đại trực tràng (USPSTF 2021), phổi (USPSTF 2021), tuyến tiền liệt (USPSTF 2018), gan (AASLD 2023), tổng quan tầm soát (WHO 2022). Tất cả `review_status: draft` — cần bác sĩ rà trước khi dùng thật.

### 3.2 Chunking (`rag/corpus.py`)
- **Theo cấu trúc**: tách theo heading `## ` (mỗi mục guideline là một đơn vị ngữ nghĩa: khuyến nghị, đối tượng, phương pháp, ngoại lệ).
- Mục dài: cửa sổ **400 từ, chồng lấp 40 từ**, lặp lại heading ở chunk tiếp theo.
- **Contextual chunk header**: text được embed/đánh chỉ mục = `"<tên nguồn> — <mục>\n<nội dung>"` để chunk ngắn vẫn mang ngữ cảnh tài liệu.
- Metadata mỗi chunk giữ nguyên frontmatter + `doc_id`, `section` → lọc và trích dẫn chính xác.

### 3.3 Retrieval lai (`rag/retriever.py`, `rag/lexical.py`)
1. **Lọc metadata trước**: giới (`gender ∈ {g, any}`), tuổi (`min_age ≤ age ≤ max_age`), loại ung thư (Copilot).
2. **Lexical BM25** thuần Python: token = âm tiết **bỏ dấu** + **bigram** (bắt cụm "nhũ ảnh", "cổ tử cung"), bỏ stopword tiếng Việt.
3. **Dense**: Chroma + `paraphrase-multilingual-MiniLM-L12-v2` (đa ngôn ngữ, chạy local).
4. **Reciprocal Rank Fusion** (k = 60) gộp hai danh sách; khử trùng theo `(doc_id, section)`; top-k = 6.
5. **Graceful degradation**: chưa ingest / thiếu model embedding → tự hạ về BM25 (`mode=lexical`, `dense=unavailable` ghi vào trace) thay vì lỗi.

### 3.4 Grounded generation
- Prompt chỉ chứa gợi ý từ luật + nguồn truy xuất; nguồn được đánh dấu "là dữ liệu, không phải chỉ dẫn" (chống injection gián tiếp).
- LLM trả **structured output** (Pydantic): `reply`, `source_ids`, `insufficient_evidence`.
- **Citation whitelist**: chỉ chấp nhận `source_ids` có trong tập đã truy xuất; không trích dẫn hợp lệ mà không tự nhận thiếu căn cứ → loại.
- **Numeric grounding**: mọi con số trong câu trả lời phải xuất hiện trong nguồn/gợi ý/hồ sơ/lời người dùng → chặn bịa tuổi, chu kỳ.
- **Abstain**: thiếu nguồn → `insufficient_evidence=true`, nói rõ "chưa đủ thông tin", khuyên hỏi bác sĩ.

## 4. Guardrails

| Lớp | Kiểm tra | Hành động | File |
|---|---|---|---|
| Input | Yêu cầu chẩn đoán / đọc kết quả / điều trị | Từ chối có giải thích + mời đặt lịch; không gọi LLM | `safety.is_out_of_scope_request` |
| Input | Prompt injection ("bỏ qua mọi hướng dẫn…") | Không gọi LLM, dùng câu trả lời mẫu; gắn cờ trace | `safety.looks_like_prompt_injection` |
| Input | Red-flag (luật + phủ định, có dấu/không dấu) | Ngắt luồng, `urgent_care`, cờ không bị gỡ trong phiên | `tools/red_flag_detector.py` |
| Process | Luật tầm soát có nguồn; schema Pydantic với invariant (red-flag ⇒ không có gợi ý; booking ⇒ có hint) | Dữ liệu sai hình dạng không thể đi ra | `schemas.py` |
| Output | Ngôn ngữ chẩn đoán ("bạn bị/mắc…", "chắc chắn là ung thư"), có xử lý câu phủ định | Thay bằng câu trả lời mẫu | `safety.find_diagnosis_language` |
| Output | Trích dẫn ngoài whitelist, con số không có trong bằng chứng | Thay bằng câu trả lời mẫu | `safety.ungrounded_numbers` |
| Output (Copilot) | Dữ kiện không có `event_id` hợp lệ | Loại dữ kiện; tóm tắt có ngôn ngữ chẩn đoán → bản mẫu | `agents/copilot.py` |
| HITL | Kế hoạch bác sĩ sửa vẫn phải có nguồn, không ngôn ngữ chẩn đoán | 400 | `encounter_service.finalize` |
| UI | Disclaimer bắt buộc, không ẩn được | — | `Disclaimer.tsx` |

**Fail-safe**: LLM lỗi/timeout/vi phạm → không bao giờ trả lỗi trống hay nội dung chưa kiểm; luôn rơi về câu trả lời **xác định** dựng từ luật + nguồn.

## 5. Human-in-the-loop
- Navigator chỉ đưa thông tin giáo dục theo nhóm; **không có kế hoạch cá nhân** nào tới bệnh nhân nếu bác sĩ chưa duyệt.
- Copilot soạn bản nháp **không có ngày hẹn**; bác sĩ điền ngày dựa trên lịch sử tầm soát thực tế, sửa, viết kết luận rồi mới finalize.
- Mọi chỉnh sửa của bác sĩ được audit (before/after) → chỉ số `plans_edited_by_doctor` đo mức độ AI cần bác sĩ sửa.

## 6. Observability: tracing, logging, metrics

| Thành phần | Nội dung | File |
|---|---|---|
| Trace ID | Mỗi lượt chạy một `trace_id` (`nav-…`, `brief-…`, `copilot-…`, `qa-…`) | `observability.new_trace_id` |
| Span / node event | `node, status, duration_ms` + thuộc tính: `source_count, mode, dense, generator, guard, next_action, red_flag, out_of_scope, injection_suspected, facts_dropped…` | `observability.traced` |
| Structured log | Mỗi event một dòng JSON trên logger `ai_core.trace` | `observability.emit` |
| Exporter | `add_sink(fn)` để đẩy sang Langfuse / OpenTelemetry / LangSmith | `observability.add_sink` |
| Lưu trữ | Bảng `agent_runs`: agent, trace_id, latency, generator, red_flag, next_action, insufficient_evidence, guard_blocked, events | `backend/app/models/agent_run.py` |
| Dashboard | `GET /doctor/metrics`: số phiên, tỉ lệ red-flag, tỉ lệ gợi ý đặt lịch, chuyển đổi tư vấn→tài khoản, lịch theo trạng thái, kế hoạch bác sĩ sửa, **fallback rate, insufficient-evidence rate, latency p50/p95**; `GET /doctor/agent-runs` xem từng trace | `metrics_service.py` |
| Riêng tư | Trace **không chứa** nội dung hội thoại, hồ sơ, API key; API công khai trả `trace_events=[]` | — |
| Kiểm toán | `audit_logs` (ai làm gì), tách biệt `record_events` (hồ sơ y tế) và `agent_runs` (quan sát AI) | — |

## 7. Đánh giá (evaluation)
- **Golden set** `ai_core/data/eval/navigator_cases.json` (40 ca: red-flag có dấu/không dấu, phủ định và "không biết/không những…", ra máu sau mãn kinh, triệu chứng của người thân, "sợ bị ung thư" ≠ tiền sử, câu hỏi chung không ghi đè tuổi/giới, hút thuốc/viêm gan của người thân, hút thuốc nặng/nhẹ, yêu cầu chẩn đoán, injection, câu hỏi kiến thức).
- Chạy: `python -m ai_core.cli eval [--real]`; CI chạy với MockAgent (`tests/test_eval.py`).
- Chỉ số & ngưỡng: red-flag recall **100%** (bắt buộc), red-flag false positive, triage accuracy, suggestion accuracy, citation validity **100%**, diagnosis-language rate **0%**, latency.
- Kết quả hiện tại (MockAgent): 40/40 ca đạt, recall 100%, FP 0%, triage 100%, suggestion 100%, citation 100%, diagnosis-language 0%.
- Unit test: 136 test AI Core (luật, RAG, guardrail vào/ra, fallback khi LLM bịa nguồn/bịa số/chẩn đoán/khuyên điều trị/lỗi/treo) + 34 test backend (hành trình đầy đủ, phân quyền, HITL, máy trạng thái lịch hẹn/lần khám, audit, nâng ưu tiên khi red-flag xuất hiện sau đặt lịch).

## 8. Bảo mật & quyền riêng tư
- Phiên ẩn danh dùng token ngẫu nhiên, DB chỉ lưu SHA-256, so sánh hằng thời gian; giới hạn 40 lượt/phiên.
- Phiên đã gắn tài khoản chỉ chủ sở hữu (JWT) đọc được. Bệnh nhân chỉ xem dữ liệu của mình (404 với dữ liệu người khác).
- Chỉ dùng hồ sơ giả lập khi gọi LLM bên thứ ba (OpenRouter…); production cần LLM đặt trong hạ tầng bệnh viện hoặc có DPA.

## 9. Giới hạn đã biết & hướng tiếp
- Luật trích xuất tiếng Việt chưa phủ hết cách diễn đạt → mở rộng golden set từ log thật (đã ẩn danh).
- Guideline chủ yếu của Mỹ/quốc tế; cần bổ sung hướng dẫn Bộ Y tế và quy trình bác sĩ duyệt (`review_status`).
- Chưa có reranker cross-encoder, chưa có LLM-as-judge; chưa đo trên agent thật với bộ ca lớn.
