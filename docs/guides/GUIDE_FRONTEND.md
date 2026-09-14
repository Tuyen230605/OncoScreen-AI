# Guide: Module 3 — Frontend UI/UX

**Bạn sở hữu:** `frontend/`. **Bạn tiêu thụ:** REST API theo `API_CONTRACT.md` (mirror TS ở `src/types/api.ts`).
**Không cần chờ Backend:** `NEXT_PUBLIC_USE_MOCK_API=true` → `src/lib/api.ts` trả dữ liệu từ `src/mocks/fixtures.ts`.

## 0. Chạy lần đầu
```bash
cd frontend
npm install
cp ../.env.example .env.local     # hoặc tạo .env.local với 2 biến NEXT_PUBLIC_*
npm run dev                       # http://localhost:3000
```
(Khung chỉ có `package.json` tối thiểu — nếu muốn khởi tạo lại bằng `npx create-next-app@latest . --ts --tailwind --app --src-dir --eslint`, giữ nguyên `src/types`, `src/lib`, `src/mocks`.)

## 1. Màn hình cần làm

### Chung
- [ ] `/login` (+ đăng ký): sau login lưu token (localStorage/cookie), redirect theo role: patient → `/patient`, doctor → `/doctor`.
- [ ] Layout theo role: `src/app/patient/layout.tsx`, `src/app/doctor/layout.tsx` (guard: sai role → redirect).
- [ ] `components/Disclaimer.tsx`: hộp cảnh báo cố định, nội dung từ API (`session.disclaimer`) — **hiển thị ở mọi màn kết quả**.
- [ ] `components/RedFlagAlert.tsx`: cảnh báo đỏ, liệt kê triệu chứng + lời khuyên đi khám, giọng điệu bình tĩnh.

### Luồng bệnh nhân (`/patient/*`)
| Route | Nội dung | API |
|---|---|---|
| `/patient` | Dashboard: hồ sơ, nút "Bắt đầu đánh giá", danh sách phiên + trạng thái, reminders sắp tới | `GET /patients/me/profile`, `GET /sessions`, `GET /reminders` |
| `/patient/profile` | Form hồ sơ (tuổi, giới, tiền sử gia đình, lối sống) | `PUT /patients/me/profile` |
| `/patient/survey` | **Khảo sát động**: render `questionnaire.questions`, ẩn/hiện theo `depends_on`, gửi answers, xử lý 3 nhánh trạng thái | `POST /sessions`, `POST /sessions/{id}/answers` |
| `/patient/results/[id]` | `collecting`→ tiếp tục khảo sát; `red_flag`→ RedFlagAlert; `pending_review`→ "đang chờ bác sĩ" (poll 10s); `approved`→ bảng `final_plan` + sources + Disclaimer + reminders + link giáo dục; `rejected`→ note | `GET /sessions/{id}` |
| `/patient/reminders` | Danh sách nhắc lịch, nút "Đã tầm soát" | `GET /reminders`, `POST /reminders/{id}/complete` |
| `/patient/education/[type]` | Nội dung giáo dục | `GET /education/{type}` |

### Dashboard bác sĩ (`/doctor/*`)
| Route | Nội dung | API |
|---|---|---|
| `/doctor` | Hàng chờ `pending_review` (ưu tiên), tab tất cả, tag "khẩn" cho `red_flag` | `GET /doctor/sessions?status=` |
| `/doctor/sessions/[id]` | Hồ sơ + câu trả lời + `risk_assessment` + **`draft_plan` có thể sửa** (bảng editable: method, interval, next_due, rationale; sources chỉ đọc) → nút Duyệt / Từ chối (bắt buộc note) | `GET /sessions/{id}`, `POST /sessions/{id}/review` |
| `/doctor/patients/[id]` | Lịch sử bệnh nhân | `GET /doctor/patients/{id}` |

## 2. Kiến trúc FE
- `src/lib/api.ts`: 1 client duy nhất — `apiFetch<T>(path, init)` gắn token, parse lỗi `{detail}`; nếu `USE_MOCK_API` → route sang `mocks/`.
- `src/types/api.ts`: **mirror contract**, không tự thêm trường. Đề xuất sửa → PR `contract/*`.
- State: React hooks + SWR/TanStack Query (tuỳ chọn) cho polling `pending_review`.
- Components gợi ý: `QuestionForm`, `PlanTable` (readonly/editable prop), `SessionStatusBadge`, `SourceList`, `ReminderList`.

## 3. UX & an toàn
- Giọng điệu: bình tĩnh, không dùng từ "chẩn đoán", "bạn bị". Dùng "khuyến nghị tham khảo", "hãy trao đổi với bác sĩ".
- Màn red-flag: không hiện bất kỳ plan nào; nút to "Tìm cơ sở y tế gần nhất" (mô phỏng).
- Màn pending: giải thích rõ "bác sĩ sẽ xem xét trước khi bạn nhận kết quả".
- Responsive 390px & 1280px.

## 4. Đừng làm
- Đừng gọi `fetch` ngoài `api.ts`. Đừng định nghĩa lại type API.
- Đừng tự tính khuyến nghị ở FE (mọi nội dung y tế đến từ API).
- WebSocket là tuỳ chọn; polling đủ cho MVP.
