# 03 — Mô hình dữ liệu (mức khái niệm)

Chi tiết cột/kiểu xem `docs/protocols/DB_SCHEMA.md`. Kho tri thức **không nằm trong PostgreSQL** mà ở `ai_core/data/` (Markdown + Chroma).

```
users 1───1 patient_profiles                         (role = patient)
users 1───* consultations (patient_id, NULL khi ẩn danh)
users 1───* appointments ───0..1 consultations
appointments 1───0..1 encounters ───* reminders
users 1───* record_events      (hồ sơ xuyên suốt, timeline)
agent_runs  ─ trace từng lần gọi AI (gắn consultation / encounter / patient nếu có)
audit_logs  ─ ai làm gì trên thực thể nào

[Kho tri thức] guidelines/*.md (frontmatter: cancer_type, gender, min_age, max_age, risk_level, source, url…)
               → chunk theo mục (header ngữ cảnh) → BM25 + Chroma
               screening_rules.json (luật tầm soát → doc_id/section)  ·  red_flags.json  ·  services.json
```

| Thực thể | Thuộc tính chính | Vai trò |
|---|---|---|
| `users` | id, email, password_hash, role, full_name | Đăng nhập, phân quyền |
| `patient_profiles` | user_id, age, gender, genetics_history, lifestyle | Hồ sơ nền; điền sẵn từ phiên tư vấn |
| `consultations` | id, patient_id?, token_hash, intake, messages, last_reply, red_flag, next_action | Phiên Navigator; ẩn danh → gắn tài khoản |
| `appointments` | id, patient_id, consultation_id?, service_code, preferred/scheduled_date, reason, priority, status | Đặt lịch mô phỏng |
| `encounters` | id, appointment_id, doctor_id, status, brief, draft_plan, final_plan, clinical_notes, conclusion | Lần khám + Copilot + HITL |
| `reminders` | encounter_id, cancer_type, method, due_date, status | Nhắc tái tầm soát |
| `record_events` | patient_id, kind, summary, data, ref_type/ref_id, visibility, occurred_at | **Hồ sơ xuyên suốt** — đầu vào của Copilot, mỗi dữ kiện trong brief trỏ về `id` ở đây |
| `agent_runs` | agent, trace_id, latency_ms, generator, red_flag, next_action, insufficient_evidence, guard_blocked, events | Observability |
| `audit_logs` | actor_id?, action, entity, entity_id, before, after | Kiểm toán |

Các loại mốc (`record_events.kind`): `account.created`, `profile.updated`, `consult.summary`, `red_flag.detected`,
`appointment.requested|confirmed|cancelled|escalated`, `encounter.started`, `encounter.finalized`, `reminder.done`.

JSON `brief`, `draft_plan`, `final_plan`, `intake`, `last_reply` lưu nguyên `model_dump(mode="json")` của `ai_core.schemas`.
