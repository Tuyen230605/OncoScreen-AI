# 00 — Tổng quan dự án

## Bối cảnh & vấn đề
Nhiều người bỏ lỡ tầm soát ung thư định kỳ (vú, cổ tử cung, đại trực tràng, gan, phổi) dù thuộc nhóm nguy cơ;
kiến thức về mốc & phương pháp tầm soát còn hạn chế.

## Mục tiêu
Xây dựng **AI Agent tầm soát** với luồng: **đánh giá nguy cơ → khuyến nghị tầm soát → đặt lịch → nhắc định kỳ**,
trong đó bác sĩ là người ra quyết định cuối cùng (Human-in-the-Loop).

## Phạm vi (Scope)

### Cơ bản (bắt buộc — MVP)
- [ ] App chạy local, **2 vai trò**: bệnh nhân (patient) / bác sĩ (doctor), có đăng nhập.
- [ ] Bộ câu hỏi đánh giá nguy cơ (tuổi, giới, tiền sử gia đình, lối sống).
- [ ] Agent gợi ý **loại & mốc tầm soát có nguồn** (trích dẫn guideline từ RAG).
- [ ] Sàng lọc triệu chứng nghi ngờ (**red-flag**) → khuyến cáo đi khám sớm, dừng tư vấn.
- [ ] Đặt lịch (mô phỏng) & giáo dục dấu hiệu cảnh báo.
- [ ] Disclaimer "không chẩn đoán" trên mọi kết quả.
- [ ] **HITL**: bác sĩ duyệt/sửa bản nháp trước khi bệnh nhân thấy kết quả.

### Nâng cao (nếu còn thời gian)
- [ ] Lịch tái tầm soát cá nhân hoá & nhắc định kỳ dài hạn (scheduler).
- [ ] Memory tiền sử / nguy cơ giữa các phiên.
- [ ] Theo dõi hoàn thành tầm soát (patient đánh dấu "đã làm").
- [ ] Nội dung truyền thông theo từng loại ung thư.
- [ ] Xử lý nhóm nguy cơ cao → chuyển bác sĩ chuyên khoa.

### Ngoài phạm vi (KHÔNG làm)
- Deploy cloud, HA, multi-tenant.
- Chẩn đoán, đọc kết quả xét nghiệm / hình ảnh y khoa.
- Tích hợp HIS/EMR thật, thanh toán, SMS/email thật (chỉ mô phỏng trong app).

## Ràng buộc an toàn (không thương lượng)
| # | Ràng buộc | Nơi thực thi |
|---|---|---|
| S1 | AI **tuyệt đối không chẩn đoán ung thư**, không diễn giải kết quả tầm soát thay bác sĩ | `ai_core/guardrails`, system prompt, Disclaimer UI |
| S2 | Khuyến nghị **phải grounded** trên guideline có nguồn (RAG), chống bịa | `ai_core/rag`, mỗi item khuyến nghị có `sources[]` |
| S3 | Triệu chứng nghi ngờ (khối u, chảy máu bất thường, sụt cân nhanh…) → **ngắt luồng**, khuyến cáo đi khám, không trấn an sai | `ai_core/tools/red_flag_detector.py`, node `red_flag` |
| S4 | Kết quả cuối **chỉ được trả sau khi bác sĩ approve** | `backend/app/services/hitl_service.py`, `hitl_status` |
| S5 | Bảo mật PHI: mật khẩu hash, token, patient chỉ xem dữ liệu của mình | `backend/app/core/security.py`, dependency `require_role` |
| S6 | Truyền thông cẩn trọng, tránh gây hoảng loạn; luôn kèm disclaimer | `ai_core/guardrails/disclaimer.py`, `frontend/src/components/Disclaimer.tsx` |

## Thành viên & phân công
| Module | Thư mục | Phụ trách | Guide |
|---|---|---|---|
| 1. AI Core & Data | `ai_core/` | Tuyền | `docs/guides/GUIDE_AI_CORE.md` |
| 2. Backend & Database | `backend/` | _(điền tên)_ | `docs/guides/GUIDE_BACKEND.md` |
| 3. Frontend UI/UX | `frontend/` | _(điền tên)_ | `docs/guides/GUIDE_FRONTEND.md` |
| Tích hợp & demo | `docs/`, `scripts/` | cả nhóm | `docs/guides/GUIDE_INTEGRATION.md` |

## Tech stack
| Lớp | Công nghệ | Lý do |
|---|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind | Đề bài; tách 2 luồng patient/doctor bằng route |
| Backend | FastAPI, SQLAlchemy 2, Pydantic v2, APScheduler | Đề bài; async, tự sinh Swagger để FE bám theo |
| AI Core | LangGraph, LangChain, Chroma (vector DB file-based) | Đề bài; Chroma không cần server, phù hợp local |
| DB | PostgreSQL 16 qua `docker compose` (fallback dev: SQLite) | Đề bài; Docker giúp cả nhóm có DB giống nhau |
| LLM | Cấu hình qua env (`LLM_PROVIDER`), mặc định Anthropic `claude-opus-5` | Đổi provider không sửa code |
