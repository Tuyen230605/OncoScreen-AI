# ADR-0001: Monorepo với 3 module độc lập + contract-first

**Trạng thái:** Accepted · **Ngày:** 2026-09-14

## Bối cảnh
3 thành viên làm 3 khối song song, thời gian ngắn, dễ conflict và dễ "chờ nhau".

## Quyết định
- 1 repo, 3 thư mục `ai_core/`, `backend/`, `frontend/`, mỗi thư mục có owner rõ ràng (`OWNERSHIP.md`).
- Giao tiếp giữa khối qua 2 contract cố định viết trước khi code: `AI_CORE_CONTRACT.md` và `API_CONTRACT.md`.
- Mỗi khối có mock của khối kế bên để chạy độc lập.

## Hệ quả
+ Không chờ nhau; conflict gần như chỉ xảy ra trong file contract (được kiểm soát bằng PR `contract/*`).
− Sửa contract tốn công (3 nơi) → khuyến khích chốt kỹ ở M1.
