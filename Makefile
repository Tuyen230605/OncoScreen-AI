# Lệnh tắt cho dev. Trên Windows dùng Git Bash hoặc chạy lệnh tương ứng trong scripts/
.PHONY: setup ai backend frontend ingest test lint

setup:            ## Cài đặt cả 3 khối
	cd ai_core && pip install -e ".[dev]"
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

ingest:           ## Nạp guideline vào vector DB
	cd ai_core && python scripts/ingest.py

backend:          ## Chạy FastAPI
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:         ## Chạy Next.js
	cd frontend && npm run dev

test:             ## Test toàn bộ
	cd ai_core && pytest -q
	cd backend && pytest -q
	cd frontend && npm test --if-present

lint:
	cd ai_core && ruff check .
	cd backend && ruff check .
	cd frontend && npm run lint
