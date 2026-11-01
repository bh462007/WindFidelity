.PHONY: dev test lint

dev:
	cd backend && uvicorn app.main:app --reload --port 8000

test:
	pytest -q

lint:
	ruff check backend