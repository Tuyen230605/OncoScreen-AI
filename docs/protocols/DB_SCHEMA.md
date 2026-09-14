# Protocol: Database Schema (PostgreSQL / SQLite)

**Chủ sở hữu:** Backend. **Nguồn sự thật:** `backend/app/models/*.py` + Alembic migrations.
Kiểu JSON: dùng `sqlalchemy.JSON` (chạy được cả Postgres lẫn SQLite; trên Postgres tự map JSONB nếu muốn tối ưu sau).

## users
| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | `uuid4()` |
| email | VARCHAR(255) UNIQUE NOT NULL | lower-case |
| password_hash | VARCHAR(255) NOT NULL | bcrypt |
| full_name | VARCHAR(255) NOT NULL | |
| role | VARCHAR(16) NOT NULL | `patient` \| `doctor` |
| created_at | TIMESTAMP | default now |

## patient_profiles
| Cột | Kiểu | Ghi chú |
|---|---|---|
| user_id | UUID PK FK→users.id | 1-1 |
| age | INT NOT NULL | |
| gender | VARCHAR(16) NOT NULL | |
| genetics_history | JSON | `["breast_cancer_mother", ...]` mã hoá theo `questionnaire.json` |
| lifestyle | JSON | free-form dict |
| lifestyle_score | FLOAT NULL | AI Core tính (tuỳ chọn) |
| updated_at | TIMESTAMP | |

## screening_sessions
| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| patient_id | UUID FK→users.id NOT NULL | index |
| doctor_id | UUID FK→users.id NULL | gán khi review |
| status | VARCHAR(32) NOT NULL | `SessionStatus` enum, index |
| questionnaire | JSON NULL | snapshot bộ câu hỏi đã hỏi |
| answers | JSON NOT NULL default `[]` | `Answer[]` |
| red_flags | JSON NULL | `RedFlagResult` |
| risk_assessment | JSON NULL | |
| draft_plan | JSON NULL | `ScreeningPlan` từ AI |
| final_plan | JSON NULL | `ScreeningPlan` sau khi bác sĩ duyệt |
| doctor_note | TEXT NULL | |
| trace_id | VARCHAR(64) NULL | id trace của AI Core để debug |
| reviewed_at | TIMESTAMP NULL | |
| created_at / updated_at | TIMESTAMP | |

## reminders
| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| session_id | UUID FK→screening_sessions.id | |
| patient_id | UUID FK→users.id | index |
| cancer_type | VARCHAR(32) | |
| method | VARCHAR(255) | |
| due_date | DATE NOT NULL | index |
| status | VARCHAR(16) | `scheduled` \| `due` \| `done` \| `skipped` |
| message | TEXT NULL | nội dung nhắc (sinh khi due) |
| completed_at | DATE NULL | |
| created_at | TIMESTAMP | |

## audit_logs
| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | UUID PK | |
| session_id | UUID FK NULL | |
| actor_id | UUID FK→users.id | |
| action | VARCHAR(64) | `session.create`, `session.answer`, `session.approve`, `session.reject`, `plan.edit`, `reminder.complete` |
| before | JSON NULL | |
| after | JSON NULL | |
| created_at | TIMESTAMP | |

## Migration
- Dùng Alembic: `alembic revision --autogenerate -m "..."` → `alembic upgrade head`.
- Dev nhanh với SQLite: `app/database.py` có `Base.metadata.create_all()` khi `DATABASE_URL` là sqlite (không cần alembic).
- **Không** sửa migration đã merge; tạo migration mới.
