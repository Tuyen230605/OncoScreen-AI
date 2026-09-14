# 03 — Mô hình dữ liệu (mức khái niệm)

Chi tiết cột/kiểu xem `docs/protocols/DB_SCHEMA.md`. Knowledge base **không nằm trong PostgreSQL** mà trong Chroma (AI Core sở hữu).

```
users 1───1 patient_profiles          (chỉ role=patient)
users 1───* screening_sessions (patient_id)
users 1───* screening_sessions (doctor_id, nullable — gán khi duyệt)
screening_sessions 1───* reminders
screening_sessions 1───* audit_logs

[Chroma] knowledge_base: chunks của guideline,
         metadata {cancer_type, source, section, min_age, max_age, gender, risk_level}
```

| Thực thể | Thuộc tính chính | Vai trò |
|---|---|---|
| `users` | id, email, password_hash, role(patient/doctor), full_name | Đăng nhập, phân quyền |
| `patient_profiles` | user_id, age, gender, genetics_history(json), lifestyle(json), lifestyle_score | Ngữ cảnh đầu vào cho RAG |
| `screening_sessions` | id, patient_id, doctor_id, status, answers(json), risk_assessment(json), draft_plan(json), final_plan(json), red_flags(json), doctor_note, reviewed_at | Log toàn bộ phiên, phục vụ HITL + audit |
| `reminders` | id, session_id, patient_id, cancer_type, method, due_date, status(scheduled/due/done/skipped) | Nhắc lịch định kỳ |
| `audit_logs` | id, session_id, actor_id, action, before(json), after(json), created_at | Kiểm toán thay đổi |
| `knowledge_base` (Chroma) | id, embedding, text, metadata | Nguồn sự thật cho khuyến nghị |

JSON `draft_plan` / `final_plan` tuân theo `ScreeningPlan` trong `AI_CORE_CONTRACT.md` — **cùng một schema**, backend chỉ lưu nguyên, không tách bảng.
