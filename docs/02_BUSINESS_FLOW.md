# 02 — Luồng nghiệp vụ cốt lõi

## Luồng chính (happy path + red-flag)

| Bước | Actor | Hành động | Khối xử lý | Kết quả / trạng thái |
|---|---|---|---|---|
| 1 | Patient | Đăng ký/đăng nhập, điền hồ sơ (tuổi, giới, tiền sử gia đình, lối sống) | FE → BE `/auth`, `/patients/me/profile` | `patient_profiles` |
| 2 | Patient | Bấm "Bắt đầu đánh giá" | BE `POST /sessions` → AI `get_questionnaire(profile)` | session `collecting`, trả bộ câu hỏi động |
| 3 | Patient | Trả lời câu hỏi (có thể nhiều vòng) | BE `POST /sessions/{id}/answers` | lưu `answers` |
| 4 | System | **Red-flag detector** chạy ngay trên mỗi lần nộp câu trả lời | AI `check_red_flags(answers)` | nếu có → `red_flag`, dừng; FE hiển thị cảnh báo đi khám chuyên khoa |
| 5 | System | Không red-flag & đủ dữ liệu → chạy LangGraph: retrieve guideline (RAG) → recommend → draft | AI `run_screening(ctx)` | `draft_plan` + `risk_assessment`, session `pending_review` |
| 6 | Doctor | Vào dashboard, xem hàng chờ, mở phiên, xem draft + nguồn trích dẫn, **sửa / duyệt / từ chối** | FE `/doctor/*` → BE `POST /sessions/{id}/review` | `approved` (`final_plan`) hoặc `rejected` |
| 7 | System | Khi approved: sinh `reminders` từ `final_plan.items[].next_due` | BE `hitl_service` → `scheduler` | bảng `reminders` |
| 8 | Patient | Xem kết quả chính thức + disclaimer + nội dung giáo dục + lịch nhắc | FE `/patient/results/[id]` | — |
| 9 | System | Scheduler quét reminders đến hạn → tạo thông báo (mô phỏng: ghi DB + hiển thị in-app) | BE `scheduler.py` | `reminders.status = due` |
| 10 | Patient | Đánh dấu "đã tầm soát" | BE `POST /reminders/{id}/complete` | `done`, tính mốc tiếp theo (nâng cao) |

## Quy tắc nghiệp vụ quan trọng
- **R1** Patient **không bao giờ** thấy `draft_plan`. API chỉ trả `final_plan` khi `status = approved`.
- **R2** Session `red_flag` không có plan, không vào hàng chờ duyệt (bác sĩ vẫn thấy trong danh sách, tag "khẩn").
- **R3** Mỗi item trong plan phải có `sources[]` không rỗng (guardrail chặn nếu rỗng).
- **R4** Disclaimer luôn được backend gắn vào response kết quả; FE hiển thị bắt buộc, không ẩn được.
- **R5** Bác sĩ sửa plan → lưu `final_plan` khác `draft_plan`, ghi `audit_logs` (ai sửa, sửa gì, khi nào).
- **R6** Ngôn ngữ trả lời của agent: tiếng Việt, giọng điệu bình tĩnh, không gây hoảng loạn.

## Ví dụ kịch bản demo (dùng cho báo cáo)
1. **Nữ 45 tuổi, mẹ bị ung thư vú** → không red-flag → draft: nhũ ảnh hàng năm từ 40, cân nhắc MRI; bác sĩ duyệt → reminder.
2. **Nam 55 tuổi, hút thuốc 30 gói-năm** → draft: LDCT phổi hàng năm + nội soi đại tràng; bác sĩ sửa khoảng cách → approved.
3. **Bất kỳ ai khai "sờ thấy khối u ở vú"** → red-flag → ngắt, cảnh báo đi khám ngay, không có plan.

## Sequence diagram (một phiên đầy đủ)

```
Patient(FE)        Backend                 AI Core                 Doctor(FE)
   │  POST /sessions   │                       │                        │
   │──────────────────►│ get_questionnaire()   │                        │
   │                   │──────────────────────►│                        │
   │  {questions}      │◄──────────────────────│                        │
   │◄──────────────────│                       │                        │
   │ POST /answers     │                       │                        │
   │──────────────────►│ check_red_flags()     │                        │
   │                   │──────────────────────►│                        │
   │                   │◄─── none ─────────────│                        │
   │                   │ run_screening()       │                        │
   │                   │──────────────────────►│ LangGraph+RAG          │
   │                   │◄─── draft_plan ───────│                        │
   │ {pending_review}  │ status=pending_review │                        │
   │◄──────────────────│                       │   GET /sessions?status=pending_review
   │                   │◄───────────────────────────────────────────────│
   │                   │   POST /sessions/{id}/review {approve, final_plan}
   │                   │◄───────────────────────────────────────────────│
   │                   │ status=approved, create reminders              │
   │ GET /sessions/{id}│                       │                        │
   │──────────────────►│                       │                        │
   │ {final_plan, disclaimer, reminders}       │                        │
   │◄──────────────────│                       │                        │
```
