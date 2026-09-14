# Guide: Tích hợp & Demo

## Thứ tự ghép nối
1. **FE ↔ BE (MockAgent)** — M1. BE chạy `USE_MOCK_AGENT=true`; FE tắt `NEXT_PUBLIC_USE_MOCK_API`. Đi hết 3 kịch bản.
2. **BE ↔ AI thật** — M2. `USE_MOCK_AGENT=false`, đã `python scripts/ingest.py`. Kiểm tra `GET /health` → `agent:"real"`.
3. **End-to-end** — M2/M3. Seed data → login patient → khảo sát → login doctor → duyệt → patient xem kết quả → reminder.

## Checklist chạy full hệ thống
```bash
# Terminal 0
docker compose up -d                       # PostgreSQL
# Terminal 1
cd ai_core && pip install -e . && python scripts/ingest.py
# Terminal 2
cd backend && python scripts/seed.py && uvicorn app.main:app --reload
# Terminal 3
cd frontend && npm run dev
```
Hoặc `scripts/dev-all.ps1` (Windows).

## Tài khoản demo (seed)
| Role | Email | Mật khẩu |
|---|---|---|
| doctor | doctor@demo.vn | 123456 |
| patient | lan@demo.vn (nữ 45, mẹ ung thư vú) | 123456 |
| patient | hung@demo.vn (nam 55, hút thuốc) | 123456 |

## Kịch bản demo cho báo cáo
Theo `02_BUSINESS_FLOW.md` mục "Kịch bản demo". Quay video ~3 phút: 1) patient khảo sát → pending; 2) doctor sửa & duyệt;
3) patient thấy kết quả + disclaimer + reminder; 4) case red-flag.

## Sự cố thường gặp
| Triệu chứng | Nguyên nhân | Cách xử |
|---|---|---|
| Backend không kết nối được DB | container chưa chạy | `docker compose up -d`, kiểm tra `docker compose ps` |
| `ModuleNotFoundError: ai_core` | chưa `pip install -e ../ai_core` trong venv backend | cài lại |
| 502 từ `/sessions/{id}/answers` | AI Core lỗi (thiếu key, vector store trống) | xem log backend, chạy ingest, kiểm tra `.env` |
| FE lỗi CORS | `CORS_ORIGINS` thiếu `http://localhost:3000` | sửa `.env` |
| Patient thấy `draft_plan` | serializer sai role | bug nghiêm trọng — xem `test_visibility.py` |
