# ADR-0003: Chroma làm vector DB; PostgreSQL chính, SQLite fallback dev

**Trạng thái:** Accepted · **Ngày:** 2026-09-14

## Bối cảnh
Đề bài yêu cầu PostgreSQL cho dữ liệu có cấu trúc và một Vector DB cho guideline. Nhóm dùng Docker để mọi người có PostgreSQL giống nhau.

## Quyết định
- Vector DB: **Chroma** persist ra thư mục (`VECTOR_STORE_DIR`), do AI Core sở hữu hoàn toàn. Không dùng pgvector để AI Core không phụ thuộc DB của backend.
- Dữ liệu ứng dụng: **PostgreSQL 16** chạy bằng `docker compose up -d` (dev + demo + nộp). **SQLite** vẫn được hỗ trợ qua `DATABASE_URL` cho test/CI và dev nhanh — models dùng kiểu `JSON` chung để chạy cả hai.

## Hệ quả
+ AI Core chạy độc lập; DB dựng bằng 1 lệnh, không lệch phiên bản giữa máy.
− Test tự động chạy trên SQLite (CI) nên vẫn cần chạy tay trên Postgres trước khi nộp (kiểu JSON, UUID).
