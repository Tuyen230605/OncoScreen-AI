# Protocol: Coding Conventions

## Chung
- Identifier, tên file, commit: **tiếng Anh**. Nội dung hiển thị cho người dùng, nội dung y tế, comment giải thích nghiệp vụ: **tiếng Việt** được.
- Không hard-code secret/URL — đọc từ env (`.env.example` là danh mục biến).
- Mỗi module public có docstring ngắn nói "làm gì, input, output".
- Log bằng `logging` (Python) / `console.*` chỉ khi dev (TS). Không log PHI (email, câu trả lời bệnh nhân) ở mức INFO.

## Python (ai_core, backend)
- Python ≥ 3.11. Type hints bắt buộc ở hàm public. Pydantic v2 (`model_validate`, `model_dump`).
- Format/lint: `ruff format` + `ruff check` (cấu hình trong `pyproject.toml`). Line length 120.
- Import order: stdlib → third-party → local. Không `from x import *`.
- Test: `pytest`, file `tests/test_<module>.py`, đặt cạnh package. Test không gọi LLM thật (mock/patch).
- AI Core: mọi prompt để trong `ai_core/ai_core/prompts.py` (không rải rác trong node) để dễ audit an toàn.
- Backend: router mỏng → service dày. Router chỉ parse/validate/gọi service/trả response. Logic nghiệp vụ nằm trong `services/`.

## TypeScript (frontend)
- `strict: true`. Không `any` (dùng `unknown` rồi narrow).
- Component: function component + hooks; file `PascalCase.tsx`; 1 component/file.
- Gọi API **chỉ** qua `src/lib/api.ts`. Không `fetch` trực tiếp trong component.
- Kiểu dữ liệu API **chỉ** từ `src/types/api.ts`. Không định nghĩa lại.
- Tailwind cho style; không CSS module trừ khi cần.
- Text hiển thị tiếng Việt; disclaimer dùng component `Disclaimer` (không tự viết lại).

## An toàn y tế trong code (checklist khi review)
- [ ] Có đường nào AI trả kết quả cho patient mà không qua approve không? → phải không có.
- [ ] Prompt có câu cấm chẩn đoán / diễn giải kết quả không?
- [ ] Red-flag có chạy **trước** khi gọi LLM không?
- [ ] Mỗi PlanItem có `sources` không?
- [ ] Disclaimer có hiển thị trên màn kết quả không?
