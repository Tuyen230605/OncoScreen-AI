# Protocol: Quyền sở hữu thư mục (Ownership)

Mục đích: ai cũng biết mình được sửa gì, ai review gì → không giẫm chân, không conflict.

| Đường dẫn | Owner | Ai được sửa | Review bởi |
|---|---|---|---|
| `ai_core/**` | Tuyền (AI) | AI | BE |
| `ai_core/ai_core/schemas.py` | AI | **contract** — PR `contract/*` | cả 3 |
| `ai_core/ai_core/mock.py` | AI | AI (BE có thể đề xuất thêm case) | BE |
| `backend/**` | BE | BE | FE hoặc AI |
| `backend/app/schemas/**` | BE | phải khớp `API_CONTRACT.md` | FE |
| `frontend/**` | FE | FE | BE |
| `frontend/src/types/api.ts` | FE | **contract** — khớp `API_CONTRACT.md` | BE |
| `docs/protocols/AI_CORE_CONTRACT.md` | AI | PR `contract/*` | cả 3 |
| `docs/protocols/API_CONTRACT.md` | BE | PR `contract/*` | cả 3 |
| `docs/protocols/DB_SCHEMA.md` | BE | BE | AI |
| `docs/guides/GUIDE_<X>.md` | owner khối X | owner X | ai cũng được góp ý |
| `docs/0*.md`, `README.md`, `.env.example`, `docker-compose.yml`, `Makefile`, `scripts/` | cả nhóm | PR nhỏ, riêng | 1 người khác |
| `topic/` | — | **không sửa** | — |

`.github/CODEOWNERS` phản ánh bảng này (điền GitHub handle thật vào).
