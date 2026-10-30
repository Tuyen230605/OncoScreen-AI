# ai_core — Module 1: AI Core & Data

Owner: **Tuyền**. Hướng dẫn: [docs/guides/GUIDE_AI_CORE.md](../docs/guides/GUIDE_AI_CORE.md).
Contract: [docs/protocols/AI_CORE_CONTRACT.md](../docs/protocols/AI_CORE_CONTRACT.md) ⇄ `ai_core/schemas.py`.
Bản đồ file: [FILE_MAP.md](FILE_MAP.md). Kỹ thuật độ tin cậy: [docs/05_AGENT_RELIABILITY.md](../docs/05_AGENT_RELIABILITY.md).

Hai agent dùng chung lõi:
- **Navigator** (`agents/navigator.py`) — người dân hỏi về tầm soát, không cần tài khoản: luật tầm soát có nguồn, red-flag ngắt luồng, điều hướng đặt lịch.
- **Clinical Copilot** (`agents/copilot.py`) — bác sĩ: tóm tắt hồ sơ xuyên suốt (dữ kiện truy vết `event_id`), gợi ý guideline, bản nháp kế hoạch để duyệt.

```bash
pip install -e ".[dev,local-embed,openai]"   # từ thư mục ai_core
pytest -q                                    # luật, RAG, guardrail, fallback, hồi quy tiếng Việt, eval
python -m ai_core.cli demo                   # MockAgent: Navigator + Copilot brief (ca nữ 45 tuổi)
python -m ai_core.cli demo --case lung|red-flag|ask
python -m ai_core.cli eval                   # golden set 40 ca (thêm --real để đo với LLM)
python scripts/ingest.py                     # nạp data/guidelines → Chroma (tuỳ chọn; thiếu thì dùng BM25)
python -m ai_core.cli demo --real            # agent thật (cần LLM key)
```

Backend chỉ import `ai_core.api`, `ai_core.schemas` (và `ai_core.guardrails` để kiểm kế hoạch bác sĩ sửa).

`MockAgent` chạy **cùng pipeline** với agent thật (luật, red-flag, BM25, guardrail, tracing) nhưng không gọi LLM và không cần
vector store — hành vi an toàn giống hệt, chỉ khác bước sinh văn bản. Kho guideline (`data/guidelines/`) hiện có 8 bản tóm tắt
ở trạng thái `review_status: draft`: cần bác sĩ rà soát trước khi dùng với người bệnh thật.
