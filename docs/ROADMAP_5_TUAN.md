# OncoScreen AI — Lộ trình công việc 5 tuần

> Phiên bản: 1.0  
> Phạm vi: 3 thành viên và hoạt động chung của nhóm  
> Mục tiêu: hoàn thiện MVP local với AI Agent hỗ trợ tầm soát, bác sĩ duyệt kết quả, reminder và demo end-to-end.

## 1. Phân công thành viên

| Thành viên | Vai trò | Phạm vi sở hữu |
|---|---|---|
| Thành viên 1 — Tuyến | AI Core & Data | `ai_core/`, guideline, RAG, LangGraph, guardrails, MockAgent |
| Thành viên 2 | Backend & Database | `backend/`, FastAPI, database, auth, HITL, scheduler |
| Thành viên 3 | Frontend UI/UX | `frontend/`, patient flow, doctor dashboard, responsive UI |

## 2. Mục tiêu chung theo tuần

| Tuần | Mục tiêu nhóm | Đầu ra bắt buộc |
|---|---|---|
| 1 | Chạy được nền tảng | FE/BE giao tiếp được qua MockAgent; auth và contract ổn định |
| 2 | Hoàn thiện MVP mock | Patient khảo sát; doctor xem, duyệt/từ chối; có kiểm soát quyền |
| 3 | Tích hợp AI thật | LangGraph + RAG tạo draft plan có nguồn; BE lưu được kết quả |
| 4 | Hardening và nghiệp vụ phụ | Reminder, education, audit, guardrail, responsive |
| 5 | Đóng gói và nghiệm thu | Full test, build, seed, video demo, báo cáo |

---

## 3. Lộ trình Thành viên 1 — AI Core & Data

### Tuần 1 — Ổn định contract và MockAgent

**Công việc**

- Kiểm tra `schemas.py`, các invariant của `ScreeningResult`, `ScreeningPlan`, `RedFlagResult`.
- Chạy và bổ sung test schema.
- Kiểm tra questionnaire động và `depends_on`.
- Kiểm tra detector red-flag rule-based.
- Chuẩn hóa ba case mock: bình thường, hút thuốc nguy cơ phổi, red-flag.

**Đầu ra**

- `MockAgent` trả đúng schema.
- Mỗi `PlanItem` có ít nhất một source.
- Red-flag không bao giờ trả screening plan.
- Có tối thiểu 5 test red-flag và 5 test không false-positive.

### Tuần 2 — Fixture và khả năng tích hợp

**Công việc**

- Ổn định questionnaire dùng cho FE.
- Bổ sung source fixture cho breast, lung, colorectal, cervical.
- Kiểm tra `missing_questions()` với câu hỏi phụ thuộc.
- Đảm bảo trace ID và ngày `next_due` có thể tái lập trong test.
- Hỗ trợ Backend xử lý các payload mock.

**Đầu ra**

- Backend chạy được toàn bộ session flow bằng MockAgent.
- FE có dữ liệu nhất quán cho collecting, red_flag và pending_review.

### Tuần 3 — AI thật

**Công việc**

- Implement node `assess_risk`.
- Implement RAG ingest và retriever có lọc giới tính/độ tuổi/nguy cơ.
- Implement `screening_recommender` với structured output.
- Hoàn thiện LangGraph: collect → red_flag → assess → retrieve → recommend → guardrail.
- Bổ sung guideline có metadata frontmatter.

**Đầu ra**

- `USE_MOCK_AGENT=false` chạy được.
- `ScreeningResult` có risk assessment, draft plan và source thật.
- Lỗi AI được đóng gói thành `AgentError`.

### Tuần 4 — An toàn, education và đánh giá

**Công việc**

- Implement education content từ guideline.
- Hoàn thiện guardrail chống ngôn ngữ chẩn đoán.
- Thêm retry một lần khi LLM trả plan sai.
- Tạo 10 ca đánh giá nội bộ.
- Kiểm tra mọi recommendation đều grounded trên source.

**Đầu ra**

- Không có plan thiếu source.
- Không có nội dung khẳng định chẩn đoán.
- Có kết quả eval và tài liệu kiến trúc AI.

### Tuần 5 — Đóng gói AI

**Công việc**

- Chạy toàn bộ test AI Core.
- Chốt prompt, guideline và cấu hình provider.
- Viết phần AI/RAG/guardrail trong báo cáo.
- Hỗ trợ nhóm xử lý lỗi trong demo.

**Đầu ra**

- AI Core chạy độc lập theo guide.
- Có JSON/log kết quả eval.
- Có nội dung báo cáo và phần trình bày AI.

---

## 4. Lộ trình Thành viên 2 — Backend & Database

### Tuần 1 — Nền tảng API

**Công việc**

- Cài dependency và xác nhận SQLite/PostgreSQL.
- Hoàn thiện config, database, model và migration.
- Kiểm tra bcrypt, JWT, role guard.
- Hoàn thiện register/login/me.
- Chạy `/health` và Swagger.

**Đầu ra**

- Backend khởi động được.
- Auth hoạt động với patient và doctor.
- DB tạo được từ trạng thái trống.

### Tuần 2 — Session và HITL với MockAgent

**Công việc**

- Hoàn thiện profile API.
- Hoàn thiện tạo session và submit answers từng phần.
- Kiểm tra merge theo `question_id`.
- Áp dụng visibility rule: patient không thấy draft plan.
- Hoàn thiện doctor queue và approve/reject.

**Đầu ra**

- Flow `collecting → red_flag/pending_review` hoạt động.
- Doctor approve tạo `final_plan`.
- Doctor reject bắt buộc có note.
- Patient khác không đọc được session.

### Tuần 3 — Kết nối AI thật

**Công việc**

- Chuyển sang `USE_MOCK_AGENT=false`.
- Gọi AI trong threadpool.
- Map `AgentError` thành HTTP 502.
- Lưu risk assessment, draft plan, red flags và trace ID.
- Kiểm tra serialization bằng schema chung.

**Đầu ra**

- Backend nhận được output AI thật.
- Không trả draft plan cho patient.
- Swagger khớp với API contract.

### Tuần 4 — Reminder, audit và hardening

**Công việc**

- Hoàn thiện scheduler.
- Chuyển reminder `scheduled → due`.
- Hoàn thiện complete reminder.
- Ghi audit log cho approve, reject, edit plan, complete reminder.
- Hoàn thiện seed data, CORS và test quyền.

**Đầu ra**

- Approve tạo reminder.
- Scheduler cập nhật reminder đến hạn.
- Có dữ liệu demo cho 1 doctor và 2 patient.
- Test visibility/HITL/auth pass.

### Tuần 5 — Đóng gói Backend

**Công việc**

- Chạy full backend test.
- Kiểm tra migration từ DB trống.
- Kiểm tra manual flow với PostgreSQL.
- Hoàn thiện README và phần Backend/Database trong báo cáo.
- Hỗ trợ quay demo.

**Đầu ra**

- Backend chạy được theo hướng dẫn một lần.
- Có seed và bộ test hoàn chỉnh.
- Không còn lỗi nghiêm trọng về quyền truy cập dữ liệu.

---

## 5. Lộ trình Thành viên 3 — Frontend UI/UX

### Tuần 1 — Auth và khung ứng dụng

**Công việc**

- Hoàn thiện login/đăng ký.
- Lưu token và user.
- Redirect theo role.
- Hoàn thiện layout patient/doctor và role guard.
- Kiểm tra mock API và TypeScript.

**Đầu ra**

- Patient vào được `/patient`.
- Doctor vào được `/doctor`.
- Sai role bị redirect.
- `npm run typecheck` pass.

### Tuần 2 — Patient flow

**Công việc**

- Dashboard patient.
- Profile form.
- Survey động theo questionnaire.
- Gửi answers từng phần.
- Màn kết quả cho collecting, red_flag và pending_review.

**Đầu ra**

- Patient hoàn thành khảo sát với MockAgent.
- Red-flag hiển thị cảnh báo và không hiển thị plan.
- Pending hiển thị thông báo chờ bác sĩ.

### Tuần 3 — Doctor flow

**Công việc**

- Dashboard hàng chờ doctor.
- Session detail.
- Hiển thị risk assessment và sources.
- Bảng draft plan editable.
- Approve/reject và note.

**Đầu ra**

- Doctor sửa được method, interval, next_due, rationale.
- Doctor duyệt được plan.
- Patient nhận được final plan sau approve.

### Tuần 4 — Reminder, education và UX

**Công việc**

- Màn reminders.
- Nút complete reminder.
- Màn education.
- Disclaimer ở mọi màn kết quả.
- Polling pending.
- Responsive 390px và 1280px.

**Đầu ra**

- Patient thấy reminder sau approve.
- Patient đọc được nội dung giáo dục.
- Giao diện không vỡ trên mobile.

### Tuần 5 — Polish và demo

**Công việc**

- Chạy mock API và API thật.
- Sửa lỗi UX/copy/accessibility.
- Chạy build, lint, typecheck.
- Chuẩn bị video demo.
- Viết phần Frontend trong báo cáo.

**Đầu ra**

- `npm run build` pass.
- Demo được ba kịch bản bắt buộc.
- Giao diện sẵn sàng trình bày.

---

## 6. Công việc chung của cả nhóm

### Hàng tuần

- Họp 30 phút cuối tuần.
- Mỗi người demo phần đã làm.
- Ghi blocker và quyết định contract.
- Kiểm tra các thay đổi có ảnh hưởng module khác.

### Mốc tích hợp

| Mốc | Điều kiện nghiệm thu |
|---|---|
| Cuối tuần 1 | Login, profile, tạo session và mock questionnaire chạy được |
| Cuối tuần 2 | Patient khảo sát → doctor duyệt/từ chối bằng MockAgent |
| Cuối tuần 3 | Flow trên chạy với AI thật và guideline thật |
| Cuối tuần 4 | Có reminder, education, audit và responsive UI |
| Cuối tuần 5 | Full test/build, seed demo, video và báo cáo hoàn chỉnh |

### Ba kịch bản nghiệm thu bắt buộc

1. Nữ 45 tuổi, tiền sử gia đình ung thư vú → draft plan → bác sĩ duyệt → patient xem final plan và reminder.
2. Nam 55 tuổi, hút thuốc từ 20 gói-năm → có recommendation phổi → bác sĩ chỉnh và duyệt.
3. Có triệu chứng red-flag → dừng tư vấn, hiển thị cảnh báo, không có plan và không tạo reminder.

## 7. Quy tắc làm việc

- FE dùng `NEXT_PUBLIC_USE_MOCK_API=true` để không chờ Backend.
- BE dùng `USE_MOCK_AGENT=true` để không chờ AI thật.
- Chỉ sửa trong module của mình.
- Thay đổi contract phải cập nhật `schemas.py`, `API_CONTRACT.md`, `AI_CORE_CONTRACT.md` và `frontend/src/types/api.ts`.
- Mỗi task phải có test happy path và ít nhất một edge case.
- Không commit secret, database local, vector store hoặc `node_modules`.
