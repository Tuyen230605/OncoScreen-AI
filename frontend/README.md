# frontend — Module 3: Next.js (patient UI + doctor dashboard)

Hướng dẫn chi tiết: [docs/guides/GUIDE_FRONTEND.md](../docs/guides/GUIDE_FRONTEND.md).
Contract: [API_CONTRACT.md](../docs/protocols/API_CONTRACT.md) ⇄ `src/types/api.ts`.

```bash
npm install
cp .env.local.example .env.local     # USE_MOCK_API=true → chạy không cần backend
npm run dev                          # http://localhost:3000
npm run typecheck && npm run lint
```

Quy tắc: gọi API **chỉ** qua `src/lib/api.ts`; type **chỉ** từ `src/types/api.ts`; mọi màn kết quả phải có `<Disclaimer/>`.
