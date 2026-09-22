# 04 — Lộ trình 5 tuần & mốc bàn giao

## Baseline sau khi chốt contract

`ai_core/ai_core/schemas.py`, `MockAgent`, API contract và type mirror của Frontend đã
được đồng bộ. FE và BE có thể phát triển song song bằng MockAgent; contract không đổi
trong các tuần sau nếu không có PR `contract/*` được cả nhóm duyệt.

| Hạng mục | Trạng thái |
|---|---|
| Schema/invariant cho `red_flag` và `pending_review` | Đã hoàn thiện |
| MockAgent với questionnaire, red-flag, screening plan và source | Đã hoàn thiện |
| FE type mirror và quy tắc API merge answers/HITL | Đã cập nhật |
| AI thật: LangGraph, RAG, assess risk, recommend | Chưa hoàn thiện |
| Backend/Frontend tích hợp đầy đủ | Chưa hoàn thiện |

## Phân công theo tuần

| Tuần | AI Core & Data — Tuyến | Backend & Database | Frontend UI/UX | Mốc chung |
|---|---|---|---|---|
| **1. Chạy được nền tảng** | Chạy test schema/mock; bổ sung test 5 red-flag và 5 ca bình thường; chốt dữ liệu questionnaire | Cài dependency, chạy SQLite/PostgreSQL; xác nhận auth, profile, session với MockAgent | Chạy mock API; hoàn thiện login, redirect role, typecheck | FE/BE đi qua được `POST /sessions` và `POST /answers` với mock |
| **2. MVP MockAgent** | Kiểm tra đủ 3 ca chuẩn; chuẩn hóa source fixture và trace ID; hỗ trợ BE debug | Hoàn thiện visibility, merge answers, status transition và HITL approve/reject | Hoàn thiện survey động, patient result, doctor queue và review form | Chạy đủ happy path và red-flag bằng MockAgent |
| **3. AI thật** | Implement assess risk, RAG ingest/retriever, recommender, LangGraph và guideline tối thiểu breast/lung/colorectal/cervical | Đổi `USE_MOCK_AGENT=false`, xử lý lỗi AI/502, lưu risk/draft/trace đúng schema | Hiển thị nguồn, risk assessment, polling pending và lỗi AI | Chạy được patient → AI thật → doctor review |
| **4. Reminder & hardening** | Implement education, guardrail retry, eval 10 ca và kiểm tra grounded sources | Hoàn thiện scheduler, reminder due/complete, audit log, seed và test phân quyền | Hoàn thiện reminders, education, disclaimer, red-flag UI, responsive | Ba kịch bản trong `02_BUSINESS_FLOW.md` chạy end-to-end |
| **5. Đóng gói** | Chốt eval, prompt, tài liệu kiến trúc và phần AI trong báo cáo | Full test, migration từ DB trống, hướng dẫn chạy và phần BE/DB trong báo cáo | Build/lint/typecheck, UX polish, quay demo và phần FE trong báo cáo | Demo 3 phút, checklist DoD và bộ hồ sơ nộp hoàn chỉnh |

## Quy tắc bàn giao

- Cuối mỗi tuần, mỗi thành viên phải demo phần mình trên dữ liệu thật hoặc fixture đã ghi rõ.
- FE không chờ BE: dùng `NEXT_PUBLIC_USE_MOCK_API=true` và dữ liệu trong `src/mocks`.
- BE không chờ AI thật: dùng `USE_MOCK_AGENT=true` và chỉ import `ai_core.api`, `ai_core.schemas`.
- Mọi thay đổi schema/API/type mirror phải đi cùng một PR `contract/*` và có cả 3 thành viên review.
- Chỉ coi là hoàn thành khi test liên quan, lint/typecheck và hướng dẫn chạy thủ công đều cập nhật.

## Ba kịch bản bắt buộc khi nghiệm thu

1. Nữ 45 tuổi, tiền sử gia đình ung thư vú → draft plan → bác sĩ duyệt → patient thấy final plan và reminder.
2. Nam 55 tuổi, hút thuốc từ 20 gói-năm → có khuyến nghị item phổi → bác sĩ chỉnh và duyệt.
3. Có triệu chứng red-flag → dừng tư vấn, hiển thị cảnh báo, không có screening plan và không tạo reminder.
