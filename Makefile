# DEV
dev-up:
	docker compose -f docker-compose.dev.yml up -d
dev-down:
	docker compose -f docker-compose.dev.yml down
dev-logs:
	docker compose -f docker-compose.dev.yml logs -f
dev-logs-bot:
	docker compose -f docker-compose.dev.yml logs -f bot

# БД
migrate:
	docker compose -f docker-compose.dev.yml exec api alembic upgrade head
migrate-create:
	docker compose -f docker-compose.dev.yml exec api alembic revision --autogenerate -m "$(msg)"
db-reset:
	docker compose -f docker-compose.dev.yml exec db psql -U zapisbot -c "DROP DATABASE IF EXISTS zapisbot_dev; CREATE DATABASE zapisbot_dev;"
	make migrate
db-seed:
	docker compose -f docker-compose.dev.yml exec api python db/seed.py

# Тесты и линтер
test:
	docker compose -f docker-compose.dev.yml exec api pytest tests/ -v
test-cov:
	docker compose -f docker-compose.dev.yml exec api pytest tests/ --cov=. --cov-report=html
lint:
	ruff check . && mypy .
format:
	black . && ruff check --fix .

# Mini App
miniapp-dev:
	cd miniapp && npm run dev
miniapp-build:
	cd miniapp && npm ci && npm run build

# ngrok (для Telegram в DEV)
ngrok-api:
	ngrok http 8000
ngrok-miniapp:
	ngrok http 5173
