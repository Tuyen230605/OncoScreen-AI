# 04 — Lộ trình & mốc bàn giao

> Điền ngày thực tế vào cột "Hạn". Mỗi mốc có tiêu chí "Done" rõ ràng để tránh hiểu khác nhau.

| Mốc | Hạn | AI Core (Tuyền) | Backend | Frontend | Done khi |
|---|---|---|---|---|---|
| **M0 Khung** | 14/09/2026 | Đọc guide, `pytest` pass với mock | `uvicorn` lên Swagger, `USE_MOCK_AGENT=true` | `npm run dev` lên trang login với mock API | Cả 3 chạy độc lập |
| **M1 Contract-first** | +1 tuần | `schemas.py` chốt; `MockAgent` trả dữ liệu hợp lệ; `questionnaire.json` + `red_flags.json` | Auth + CRUD sessions + review endpoint theo API_CONTRACT (dùng MockAgent) | Màn login, khảo sát, kết quả, dashboard bác sĩ (fixtures) | FE ↔ BE ghép được với mock agent |
| **M2 AI thật** | +2 tuần | Ingest guideline vào Chroma; LangGraph đủ node; red-flag + guardrails có test | Scheduler reminders; audit log | Hiển thị nguồn trích dẫn, red-flag alert, reminders | `USE_MOCK_AGENT=false` chạy end-to-end |
| **M3 Hoàn thiện** | +3 tuần | Prompt tuning, eval nhỏ (10 ca), education content | Hardening, seed data demo, test | UX polish, disclaimer, responsive | 3 kịch bản demo chạy trơn |
| **M4 Báo cáo** | +4 tuần | Viết phần AI trong báo cáo | Viết phần BE/DB | Viết phần FE + quay video demo | Nộp |

## Phụ thuộc chéo (để không chờ nhau)
- FE cần: `API_CONTRACT.md` (có sẵn từ M0) — không cần chờ BE.
- BE cần: `AI_CORE_CONTRACT.md` + `MockAgent` (có sẵn từ M0) — không cần chờ AI.
- AI cần: không phụ thuộc ai. Chỉ cần giữ đúng `schemas.py`.

## Họp đồng bộ
- 1 lần/tuần, 30 phút: mỗi người demo phần mình chạy được, nêu blocker, đề xuất sửa contract (nếu có).
- Sửa contract chỉ chốt trong buổi này (hoặc PR được cả 3 approve).
