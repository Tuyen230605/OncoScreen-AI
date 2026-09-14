# Protocol: Definition of Done (DoD)

Một task/PR được coi là **xong** khi đủ:

## Mọi PR
- [ ] Chạy được local theo hướng dẫn trong guide của khối.
- [ ] Không phá contract (`schemas.py`, `API_CONTRACT.md`, `types/api.ts`) — hoặc là PR `contract/*` có cả 3 approve.
- [ ] Lint pass (`ruff` / `npm run lint`).
- [ ] Test liên quan pass; thêm test cho logic mới (tối thiểu happy path + 1 edge case).
- [ ] Không commit secret, file sinh ra (`vector_store/`, `.db`, `node_modules`).
- [ ] Điền PR template; mô tả **cách test thủ công**.
- [ ] Nếu đổi env → cập nhật `.env.example` + guide.

## Riêng AI Core
- [ ] Output validate được bằng schema (`ScreeningResult.model_validate` không lỗi).
- [ ] Mỗi PlanItem có ≥1 source thật từ vector DB (không phải placeholder).
- [ ] Test red-flag: ≥ 5 câu có red-flag phải bắt được, ≥ 5 câu bình thường không false-positive.
- [ ] Prompt không chứa từ ngữ chẩn đoán ("bạn bị", "bạn mắc"…); guardrail test pass.

## Riêng Backend
- [ ] Endpoint có trong Swagger `/docs`, request/response khớp `API_CONTRACT.md`.
- [ ] Test quyền: patient không thấy `draft_plan`; patient A không đọc session của B; doctor mới được review.
- [ ] Migration (nếu đổi schema) chạy được từ DB trống.

## Riêng Frontend
- [ ] Chạy được với `NEXT_PUBLIC_USE_MOCK_API=true` **và** `false`.
- [ ] Màn kết quả luôn hiển thị `Disclaimer`; màn red-flag hiển thị `RedFlagAlert`.
- [ ] Responsive tối thiểu ở 390px (điện thoại) và 1280px.
- [ ] Không có lỗi TypeScript (`npm run build` pass).

## Mốc tích hợp (M2)
- [ ] 3 kịch bản demo trong `02_BUSINESS_FLOW.md` chạy end-to-end với `USE_MOCK_AGENT=false`.
