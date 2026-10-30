# Protocol: REST API Contract (Backend ↔ Frontend)

**Base URL:** `http://localhost:8000/api/v1` · **Auth:** `Authorization: Bearer <JWT>` · **Content-Type:** `application/json`
**Nguồn sự thật:** file này + `frontend/src/types/api.ts` (mirror). Backend `app/schemas/*` phải khớp. Swagger tự sinh tại `/docs`.
**Chủ sở hữu:** Backend. Frontend tiêu thụ. Muốn đổi → PR `contract/*`, tag cả team.

## Quy ước chung
- ID: UUID string. Ngày: ISO-8601 (`2026-09-14`, `2026-09-14T08:00:00Z`).
- Lỗi: `{ "detail": string }` (400 vi phạm nghiệp vụ/guardrail, 401 chưa đăng nhập/sai token tư vấn, 403 sai role hoặc không phải bác sĩ phụ trách, 404, 409 sai trạng thái, 502 lỗi AI — thông điệp cố định, không lộ lỗi nội bộ). Lỗi kiểm tra dữ liệu đầu vào do FastAPI trả `422 { "detail": [...] }`.
- Phân trang: `?page=1&page_size=20` (`page ≥ 1`, `1 ≤ page_size ≤ 100`) → `{ items, total, page, page_size }`.
- Kiểu AI (`NavigatorReply`, `ClinicalBrief`, `ScreeningPlan`, `QuestionAnswer`…) **giống hệt** `AI_CORE_CONTRACT.md`.

## Hành trình người dùng ↔ endpoint

| Giai đoạn | Người dùng | Endpoint |
|---|---|---|
| 1. Tìm hiểu (ẩn danh) | Người dân | `/navigator/*`, `/services`, `/education/*` |
| 2. Tạo tài khoản & đặt lịch | Bệnh nhân | `/auth/register` (kèm phiên tư vấn), `/appointments` |
| 3. Khám | Bác sĩ | `/doctor/appointments/*`, `/doctor/encounters/*`, `/doctor/patients/*` |
| 4. Theo dõi | Bệnh nhân | `/patients/me/record`, `/encounters/{id}`, `/reminders` |

## 1. Navigator — công khai, không cần đăng nhập

| Method | Path | Auth | Body | Response |
|---|---|---|---|---|
| GET | `/navigator/questionnaire` | — | — | `Questionnaire` (bảng hỏi nhanh) |
| POST | `/navigator/consultations` | tuỳ chọn Bearer (patient) | — | `201 ConsultationCreated` |
| GET | `/navigator/consultations/{id}` | `X-Consult-Token` hoặc Bearer chủ sở hữu | — | `ConsultationOut` |
| POST | `/navigator/consultations/{id}/messages` | `X-Consult-Token` hoặc Bearer chủ sở hữu | `NavigatorMessageIn` | `ConsultationOut` (`last_reply` là lượt mới nhất) |
| POST | `/navigator/consultations/{id}/claim` | Bearer patient + `X-Consult-Token` | — | `ConsultationOut` (gắn phiên vào tài khoản đã có) |
| GET | `/services` | — | — | `ServiceOut[]` (danh mục dịch vụ mô phỏng) |
| GET | `/education` | — | — | `{ cancer_type, title }[]` |
| GET | `/education/{cancer_type}` | — | — | `EducationContent` |

```
NavigatorMessageIn  = { message?: string (≤2000), answers?: Answer[] }   // ít nhất một trong hai
ConsultationCreated = { access_token: string, consultation: ConsultationOut }   // token chỉ trả một lần
ConsultationOut     = { id, linked:boolean, intake: IntakeProfile, messages: {role,content,at}[],
                        last_reply: NavigatorReply|null, created_at, updated_at }
```

Quy tắc:
- Token tư vấn là chuỗi ngẫu nhiên; backend chỉ lưu SHA-256. Sai/thiếu token → 401. Phiên đã gắn tài khoản chỉ chủ sở hữu (Bearer) truy cập.
- `NavigatorReply.trace_events` luôn `[]` ở API công khai; trace đầy đủ lưu ở `agent_runs` (bác sĩ xem).
- `next_action`: `continue_chat` → tiếp tục hỏi; `suggest_booking` → FE hiển thị CTA "Tạo tài khoản để đặt lịch" với `booking_hint.service_codes`; `urgent_care` → FE hiển thị cảnh báo đỏ + CTA đặt lịch ưu tiên + gọi 115 khi nặng.
- Red-flag đã ghi nhận trong phiên không bị gỡ ở các lượt sau (fail-safe).
- Tối đa 40 lượt/phiên (429 khi vượt) để hạn chế lạm dụng.

## 2. Auth

| Method | Path | Role | Body | Response |
|---|---|---|---|---|
| POST | `/auth/register` | public | `RegisterIn` | `201 UserOut`; role `doctor` → 403 |
| POST | `/auth/login` | public | `{ email, password }` | `{ access_token, token_type:"bearer", user: UserOut }` |
| GET | `/auth/me` | any | — | `UserOut` |

`RegisterIn = { email, password (≥6), full_name, role:"patient", consultation_id?, consultation_token? }`.
Khi có phiên tư vấn hợp lệ, chưa gắn: backend gắn phiên vào tài khoản, **điền sẵn hồ sơ** (tuổi, giới, tiền sử gia đình, hút thuốc, viêm gan) nếu đủ tuổi + giới, và ghi các mốc `account.created`, `consult.summary`, `red_flag.detected` vào hồ sơ xuyên suốt. Token sai → 400.

## 3. Bệnh nhân

| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/patients/me/profile` | — | `PatientProfileOut` (404 nếu chưa có) |
| PUT | `/patients/me/profile` | `PatientProfileIn` | `PatientProfileOut` (ghi mốc `profile.updated`) |
| GET | `/patients/me/record` | — | `PatientRecordOut` (góc nhìn bệnh nhân) |
| POST | `/appointments` | `AppointmentIn` | `201 AppointmentOut` |
| GET | `/appointments` | — | `AppointmentOut[]` (của mình, mới nhất trước) |
| POST | `/appointments/{id}/cancel` | — | `AppointmentOut` (409 nếu đã completed/cancelled hoặc bác sĩ đã bắt đầu khám) |
| GET | `/encounters/{id}` | — | `EncounterOut` (góc nhìn bệnh nhân) |
| POST | `/encounters/{id}/questions` | `{ question (1–1000) }` | `QuestionAnswer` (409 nếu chưa finalized) |
| GET | `/reminders` | `?status=` | `ReminderOut[]` |
| POST | `/reminders/{id}/complete` | `{ completed_at?: date }` | `ReminderOut` |

Quy tắc đặt lịch:
- `service_code` phải có trong `/services`; `preferred_date` ≥ hôm nay; tối đa 3 lịch `requested|confirmed` đồng thời.
- `priority = urgent` khi `consultation_id` (của chính bệnh nhân) có red-flag hoặc dịch vụ là `oncology_priority`. Red-flag phát hiện **sau** khi đã đặt lịch → các lịch đang mở (`requested`/`confirmed`) của phiên đó được nâng lên `urgent` (mốc `appointment.escalated`, audit `appointment.escalate`).

**Quy tắc lộ dữ liệu (bắt buộc, có test):**
- Bệnh nhân **không bao giờ** thấy `brief`, `draft_plan`, `clinical_notes`, trace.
- `final_plan`, `conclusion`, `reminders` của encounter chỉ hiện khi `status=finalized`.
- Bệnh nhân chỉ xem dữ liệu của mình (khác chủ → 404).

## 4. Bác sĩ — Clinical Copilot & HITL

| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/doctor/appointments` | `?status=&page=` | `Page<AppointmentOut>` (urgent trước, rồi theo ngày) |
| POST | `/doctor/appointments/{id}/confirm` | `{ scheduled_date }` | `AppointmentOut` (chỉ từ `requested`) |
| POST | `/doctor/appointments/{id}/start` | — | `EncounterOut` (tạo encounter + chạy Copilot brief; idempotent) |
| GET | `/doctor/patients` | `?q=` | `PatientListItem[]` |
| GET | `/doctor/patients/{id}/record` | — | `PatientRecordOut` (đầy đủ) |
| GET | `/doctor/encounters/{id}` | — | `EncounterOut` (đầy đủ) |
| POST | `/doctor/encounters/{id}/brief` | — | `EncounterOut` (sinh lại brief từ hồ sơ mới nhất; 409 nếu finalized; 403 nếu không phải bác sĩ đã bắt đầu khám) |
| POST | `/doctor/encounters/{id}/copilot` | `{ question, history: ChatTurn[] ≤8 }` | `QuestionAnswer` |
| POST | `/doctor/encounters/{id}/finalize` | `FinalizeEncounterIn` | `EncounterOut` (409 nếu đã finalized hoặc lịch hẹn không ở trạng thái `confirmed`; 403 nếu không phải bác sĩ đã bắt đầu khám) |
| GET | `/doctor/metrics` | — | `MetricsOut` |
| GET | `/doctor/agent-runs` | `?agent=&page=` | `Page<AgentRunOut>` |
| GET | `/doctor/reminders/due` | — | `ReminderOut[]` |

`FinalizeEncounterIn = { conclusion (bắt buộc), clinical_notes?, final_plan?: ScreeningPlan|null, use_draft?: boolean }`

Quy tắc HITL:
- Không gửi `final_plan` và `use_draft != false` → dùng `draft_plan` của Copilot. `final_plan: null` hoặc `use_draft=false` mà không gửi plan → kết thúc khám không lập kế hoạch (vẫn bắt buộc `conclusion`).
- Plan gửi lên phải qua `validate_plan` (mỗi item có nguồn là tài liệu có trong kho guideline; không có ngôn ngữ chẩn đoán ở mọi trường văn bản) → vi phạm 400. `interval_months` tối đa 120 → vượt 422.
- Plan khác bản nháp (kể cả bỏ bản nháp) → audit `plan.edit` (before/after). Reminder chỉ sinh cho item có `next_due`.
- Finalize → appointment `completed`, mốc `encounter.finalized` (kèm `cancer_types`) vào hồ sơ; bệnh nhân thấy kết luận + kế hoạch.

## 5. Reminders
`ReminderOut = { id, encounter_id, patient_id, cancer_type, method, due_date, status, completed_at, message }`.
Scheduler chuyển `scheduled → due` khi tới hạn và sinh lời nhắc. Hoàn thành → tạo chu kỳ kế tiếp theo `interval_months` của kế hoạch đã duyệt (không tạo trùng); ghi mốc `reminder.done`.

## 6. Health
`GET /health` → `{ status:"ok", agent:"mock"|"real", db:"ok" }`

## Ví dụ luồng FE
```
(ẩn danh) POST /navigator/consultations → lưu {id, access_token} ở localStorage
          POST /navigator/consultations/{id}/messages {message | answers}  (lặp)
            └ next_action = suggest_booking | urgent_care → CTA → /register?consult=<id>
POST /auth/register {…, consultation_id, consultation_token} → login → POST /appointments {service_code, preferred_date, consultation_id}
doctor: GET /doctor/appointments → confirm → start (brief) → copilot → finalize
patient: GET /patients/me/record → GET /encounters/{id} (finalized) → POST /encounters/{id}/questions
```
