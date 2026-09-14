# CLAUDE.md — hướng dẫn cho AI coding assistant làm việc trong repo này

- Đọc `docs/00_OVERVIEW.md` trước khi làm bất cứ gì.
- Repo chia 3 khối độc lập: `ai_core/`, `backend/`, `frontend/`. Chỉ sửa trong khối được yêu cầu.
- **Contract là bất biến trừ khi được yêu cầu rõ**: `docs/protocols/API_CONTRACT.md`, `docs/protocols/AI_CORE_CONTRACT.md`,
  `ai_core/ai_core/schemas.py`, `frontend/src/types/api.ts`. Sửa contract → phải cập nhật đồng bộ cả 3 nơi + docs.
- Ràng buộc an toàn y tế (không được vi phạm khi viết prompt/code): AI không chẩn đoán, không diễn giải kết quả xét nghiệm,
  red-flag → ngắt luồng, mọi kết quả cuối phải qua bác sĩ duyệt, luôn kèm disclaimer.
- Python: ruff + type hints + pydantic v2. TS: strict mode. Test đặt cạnh module (`tests/`).
- Ngôn ngữ giao diện & nội dung y tế: tiếng Việt. Code/identifier: tiếng Anh.
