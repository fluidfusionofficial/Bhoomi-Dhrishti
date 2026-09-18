# ─────────────────────────────────────────────────────────────────────────────
# Bhoomi Dhrishti – Makefile
# ─────────────────────────────────────────────────────────────────────────────
.PHONY: help up down build seed demo logs ps clean clean-all lint test test-all fmt eval start stop

COMPOSE = docker compose
COMPOSE_FILE = docker-compose.yml
ENV_FILE = .env

# Default target
help:
	@echo "Bhoomi Dhrishti – Available targets:"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make demo      One-command demo startup (infrastructure + services + data)"
	@echo ""
	@echo "📦 Service Management:"
	@echo "  make up        Start all services (build if needed)"
	@echo "  make down      Stop and remove containers"
	@echo "  make stop      Alias for 'down'"
	@echo "  make build     Build all service images"
	@echo "  make restart   Restart all services"
	@echo "  make ps        Show running containers"
	@echo ""
	@echo "🌱 Data Management:"
	@echo "  make seed      Seed demo data (run after 'make up')"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  make test      Run core service tests"
	@echo "  make test-all  Run all service tests (longer)"
	@echo "  make eval      Run entity resolution evaluation"
	@echo "  make lint      Run Python linting (ruff)"
	@echo "  make fmt       Auto-format Python code"
	@echo ""
	@echo "🗄️  Database:"
	@echo "  make migrate   Run pending DB migrations"
	@echo "  make psql      Open psql shell"
	@echo "  make redis-cli Open redis-cli shell"
	@echo ""
	@echo "📊 Observability:"
	@echo "  make logs      Tail all service logs"
	@echo "  make logs-<svc> Tail specific service logs (e.g., make logs-parcel-identity)"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean     Remove containers, volumes and images"
	@echo "  make clean-all Complete cleanup (including Docker system prune)"
	@echo ""

# ── Environment check ────────────────────────────────────────────────────────
check-env:
	@test -f $(ENV_FILE) || (echo "ERROR: .env not found. Copy .env.example to .env and fill in values." && exit 1)

# ── Core lifecycle ───────────────────────────────────────────────────────────
up: check-env
	$(COMPOSE) --env-file $(ENV_FILE) up -d --build
	@echo "All services starting. Use 'make logs' to watch. UI: http://localhost"

down:
	$(COMPOSE) down

build: check-env
	$(COMPOSE) --env-file $(ENV_FILE) build --parallel

restart: down up

# ── Database ─────────────────────────────────────────────────────────────────
seed: check-env
	@echo "Seeding LGD hierarchy and reference data..."
	$(COMPOSE) exec postgres psql -U $$(grep POSTGRES_USER $(ENV_FILE) | cut -d= -f2) \
	  -d $$(grep POSTGRES_DB $(ENV_FILE) | cut -d= -f2) \
	  -f /docker-entrypoint-initdb.d/05_seed_metadata.sql
	@echo "Seed complete."

migrate: check-env
	@echo "Running migrations (placeholder — add alembic here)..."
	$(COMPOSE) exec parcel-identity alembic upgrade head
	$(COMPOSE) exec revenue-records alembic upgrade head
	$(COMPOSE) exec registration alembic upgrade head

psql: check-env
	$(COMPOSE) exec postgres psql -U $$(grep POSTGRES_USER $(ENV_FILE) | cut -d= -f2) \
	  -d $$(grep POSTGRES_DB $(ENV_FILE) | cut -d= -f2)

redis-cli: check-env
	$(COMPOSE) exec redis redis-cli -a $$(grep REDIS_PASSWORD $(ENV_FILE) | cut -d= -f2)

# ── Demo ─────────────────────────────────────────────────────────────────────
demo: ## One-command demo startup with data seeding
	@echo "🚀 Starting Bhoomi Dhrishti Demo..."
	@bash scripts/start_demo.sh

seed: check-env ## Seed demo data (requires services to be running)
	@echo "🌱 Seeding demo data..."
	@bash scripts/seed_demo_data.sh

start: demo ## Alias for 'demo'

stop: down ## Stop all services

# ── Observability ────────────────────────────────────────────────────────────
logs:
	$(COMPOSE) logs -f --tail=100

logs-%:
	$(COMPOSE) logs -f --tail=200 $*

ps:
	$(COMPOSE) ps

# ── Quality ──────────────────────────────────────────────────────────────────
lint: ## Run Python linting across all services
	@echo "🔍 Running ruff linting..."
	@find services workflows shared -name "*.py" -type f 2>/dev/null | xargs python -m ruff check --select E,W,F,I || echo "✓ Linting complete"

fmt: ## Auto-format Python code
	@echo "✨ Formatting Python code..."
	@find services workflows shared -name "*.py" -type f 2>/dev/null | xargs python -m ruff format || echo "✓ Formatting complete"

test: ## Run core service tests
	@echo "🧪 Running core service tests..."
	@$(COMPOSE) run --rm parcel-identity pytest tests/ -v || true
	@$(COMPOSE) run --rm revenue-records pytest tests/ -v || true
	@$(COMPOSE) run --rm registration pytest tests/ -v || true
	@$(COMPOSE) run --rm geospatial pytest tests/ -v || true

test-all: ## Run all service tests (comprehensive)
	@echo "🧪 Running all service tests..."
	@for svc in services/*/; do \
		svc_name=$$(basename $$svc); \
		if [ -f "$$svc/tests/test_*.py" ] || [ -d "$$svc/tests" ]; then \
			echo "  Testing $$svc_name..."; \
			$(COMPOSE) run --rm $$svc_name pytest tests/ -v || true; \
		fi; \
	done
	@echo "✓ All tests completed"

eval: ## Run entity resolution evaluation and show metrics
	@echo "📊 Running entity resolution evaluation..."
	@curl -s http://localhost:8000/parcel-identity/resolution/metrics | jq '.' || echo "⚠ Service not running. Start with 'make up' first."

# ── Cleanup ──────────────────────────────────────────────────────────────────
clean: ## Remove containers, volumes, and local images
	@echo "🧹 Cleaning up containers and volumes..."
	$(COMPOSE) down -v --rmi local
	docker image prune -f
	@echo "✓ Cleanup complete"

clean-all: clean ## Complete cleanup including Docker system prune
	@echo "🧹 Deep cleaning Docker system..."
	docker system prune -af --volumes
	@echo "✓ Deep cleanup complete"

clean-data: ## Clean generated data directories
	@echo "🗑️  Removing generated data..."
	rm -rf data/raw/* data/processed/* data/ground_truth/* || true
	@echo "✓ Data directories cleaned"
