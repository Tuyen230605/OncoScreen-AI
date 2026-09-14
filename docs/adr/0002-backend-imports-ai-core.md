# ADR-0002: Backend gọi AI Core bằng Python import, không qua HTTP

**Trạng thái:** Accepted · **Ngày:** 2026-09-14

## Bối cảnh
Đề bài yêu cầu chạy local, không deploy. Tách AI Core thành service HTTP riêng làm tăng số process, cấu hình, lỗi mạng.

## Quyết định
`ai_core` là Python package cài `pip install -e`; backend import `ai_core.api.get_agent()`. Gọi trong threadpool vì sync và chậm.

## Hệ quả
+ Đơn giản, debug 1 process, type-safe (dùng chung Pydantic schema).
− Backend và AI Core phải cùng Python version & venv tương thích.
− Nếu sau này cần tách: bọc `api.py` bằng FastAPI riêng, contract giữ nguyên.
