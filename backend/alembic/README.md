# Alembic migrations (PostgreSQL)

Khởi tạo lần đầu (BE làm ở M1):
```bash
cd backend
alembic init alembic            # nếu chưa có alembic.ini/env.py
# trong alembic/env.py: from app.database import Base; target_metadata = Base.metadata; url = settings.database_url
alembic revision --autogenerate -m "init"
alembic upgrade head
```
Dev với SQLite không cần alembic (`init_db()` tự `create_all`).
