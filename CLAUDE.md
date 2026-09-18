# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Bhoomi Dhrishti** — Integrated GIS-based Digital Public Infrastructure for Land Governance. SIH 2026, PS-26014, Ministry of Rural Development / DoLR.

Core philosophy: **federated authority + materialised non-authoritative cache**. States keep their records. This platform owns parcel identity (BDPR/ULPIN), standards, the API gateway, and analytics on inter-departmental disagreements. The platform **never asserts conclusive ownership** — India has presumptive title, not conclusive title. Every API response showing ownership data must carry `source_department`, `source_system`, `source_as_of_date`, and `data_freshness_status` (LIVE / CACHED / SYNTHETIC).

## Commands

All commands run from `bhoomi-dhrishti/` (the repo root containing `Makefile`).

```bash
# First-time setup
cp .env.example .env   # then fill in passwords

# Lifecycle
make up           # build + start all 16 services + infra
make down         # stop everything
make demo         # one-command demo (runs scripts/start_demo.sh)
make seed         # seed demo data (runs scripts/seed_demo_data.sh, services must be up)
make logs         # tail all logs
make logs-<svc>   # e.g. make logs-trust-engine

# Database
make psql         # open psql shell
make redis-cli    # open redis-cli shell
make migrate      # run Alembic migrations for core services

# Quality
make lint         # ruff check across services/ + shared/
make fmt          # ruff format (auto-fix)
make test         # pytest in parcel-identity, revenue-records, registration, geospatial
make test-all     # pytest in every service that has tests/

# Single service test (from repo root)
docker compose run --rm <service-name> pytest tests/ -v

# Data generation (requires shapely, faker, numpy, pandas)
python data/generator/generate.py --seed 42

# Frontend (from frontend/, requires Node >=20 + pnpm >=9)
pnpm install
pnpm dev:officer     # officer console on :3000
pnpm dev:citizen     # citizen PWA on :3002
pnpm dev:admin       # admin console on :3003
pnpm dev             # all three apps in parallel (via Turborepo)
pnpm lint            # ESLint across all apps/packages
pnpm type-check      # TypeScript check across all apps/packages
pnpm format          # Prettier across all TS/JSON/MD files

# Per-app filter syntax also works:
pnpm --filter @bhoomi/officer type-check
```

Frontend apps each need `frontend/apps/<app>/.env.local` — copy from `frontend/.env.example`.

## Architecture

### Backend: 16 FastAPI Microservices

Each service lives in `services/<name>/` with the same internal layout:
```
app/
  main.py       # FastAPI app, lifespan, middleware, router mounts
  config.py     # pydantic-settings Settings class
  db.py         # service-local engine (wraps bhoomi_common.db pattern)
  models/       # SQLAlchemy ORM models
  schemas/      # Pydantic request/response schemas
  routers/      # APIRouter modules (one per domain concept)
  services/     # Business logic layer (called by routers)
  modules/      # Domain-specific sub-modules (e.g. trust-engine checks)
```

All API routes are prefixed `/api/v1/<domain>`. Health is always at `GET /health`.

**Port map** (internal Docker network):
| Service | Port | Status |
|---|---|---|
| parcel-identity | 8001 | Full |
| geospatial | 8002 | Full |
| revenue-records | 8003 | Full |
| registration | 8004 | Full |
| planning-zoning | 8005 | Stub |
| fiscal | 8006 | Stub |
| utilities | 8007 | Stub |
| trust-engine | 8008 | Full |
| ml-inference | 8009 | Stub |
| citizen-services | 8010 | Full |
| audit | 8011 | Full |
| notifications | 8012 | Full |
| search | 8013 | Full |
| analytics | 8014 | Full |
| interoperability | 8015 | Full |
| satellite | 8016 | Stub |

There is also a `services/workflows/` directory for orchestration workflows (not exposed as a standalone HTTP service).

Nginx (`infrastructure/nginx/nginx.conf`) proxies external traffic; all services are reachable through it on port 80/443 at `/api/<service-short-name>/`.

### Shared Python Library (`shared/python/bhoomi_common/`)

**Import as `bhoomi_common`** (installed via `shared/python/setup.py`). Every service Dockerfile installs it.

Key modules:
- `models.py` — base Pydantic models. `ProvenanceBase` is **mandatory** for any response wrapping a sourced DB record. `BhoomiBased` (forbid extra, populate_by_name) is the base for all other schemas.
- `auth.py` — JWT verification via Keycloak JWKS. Use `get_current_actor` / `get_optional_actor` / `require_roles(["role"])` as FastAPI `Depends`. The `Actor` object carries `roles`, `state_code`, `district_code`, `purpose`.
- `db.py` — async SQLAlchemy engine + session factory. Call `init_db()` in lifespan, inject `get_db` as a dependency.
- `audit.py` — emit structured audit events to the audit service via HTTP. All data accesses and mutations **must** call `emit_audit_event()`. Use `AuditEventType` enum for event types.
- `errors.py` — standard `ErrorResponse` / `ErrorDetail` Pydantic models.
- `pagination.py` — `PaginatedResponse[T]` generic wrapper.

### Database: PostgreSQL 16 + PostGIS

Schema namespaces (defined in `infrastructure/postgres/init/01_schemas.sql`):
- `identity` — canonical parcels, aliases, lineage
- `geo` — PostGIS geometries, topology conflicts, restriction zones
- `revenue` — RoR, mutations, party registry
- `registration` — deeds, encumbrances
- `planning` — zoning, building permits, disputes
- `fiscal` — tax assessments, valuations
- `audit` — append-only partitioned event log (**no UPDATE or DELETE ever**)
- `ml` — conflict scores, entity resolution links, network anomaly flags
- `reference` — LGD hierarchy, unit conversions, code mappings

Init scripts run in order: `00_extensions.sql` → `01_schemas.sql` → `02_tables.sql` → `03_indexes.sql` → `04_functions.sql` → `05_seed_metadata.sql`.

### Frontend: Next.js 14 pnpm Monorepo (`frontend/`)

Turborepo orchestrates builds/dev across the monorepo. The frontend has its own git repo (`frontend/.git`).

Workspace structure:
- `apps/officer/` (`@bhoomi/officer`) — revenue officer / district collector console (MapLibre + Recharts + ReactFlow + framer-motion), port 3000
- `apps/citizen/` (`@bhoomi/citizen`) — citizen PWA with i18n (i18next + next-pwa), port 3002
- `apps/admin/` (`@bhoomi/admin`) — platform admin console (YAML editor for state onboarding), port 3003
- `packages/ui/` (`@bhoomi/ui`) — shared design system (Tailwind CSS + shadcn/ui + Radix primitives)
- `packages/types/` (`@bhoomi/types`) — shared TypeScript types
- `packages/map/` (`@bhoomi/map`) — MapLibre GL wrapper + PMTiles support
- `packages/api-client/` (`@bhoomi/api-client`) — typed API client

Auth: `keycloak-js` handles token refresh; all API calls include the bearer token.

### Data & Scripts

- `data/generator/` — Python mock data generator (`generate.py --seed 42`); produces parcels for TN rural + CH urban with deliberate defects for testing conflict detection.
- `data/mappings/<state>/mapping.yaml` — state-specific field mapping configs (currently `tn_rural/` and `ch_urban/`).
- `data/raw/`, `data/processed/`, `data/ground_truth/` — generated data directories (gitignored, created by generator).
- `scripts/start_demo.sh` — orchestrates infrastructure → services → health checks.
- `scripts/seed_demo_data.sh` — loads generated data into running services.
- `scripts/load_data_to_db.py` — direct DB data loader.

### Trust Engine (`services/trust-engine/`)

The most critical service. Runs deterministic rule checks against live DB tables; each check is a separate query that passes gracefully when no data exists. Risk banding: `CRITICAL` penalty=40, `HIGH`=20, `MEDIUM`=10, `LOW`=5. Band thresholds: any CRITICAL or ≥3 HIGH → HIGH band; ≥1 HIGH or ≥3 MEDIUM → MEDIUM band.

### Interoperability Service (`services/interoperability/`)

The mapping engine translates state-specific field names and value enumerations (from `data/mappings/`) to canonical Bhoomi Dhrishti schemas. Conformance tiers: **Bronze** (read-only sync), **Silver** (write-back), **Gold** (real-time bidirectional).

### Audit Service (`services/audit/`)

Append-only. The `audit` schema has no UPDATE or DELETE privileges granted to `bhoomi_app`. The audit table is partitioned by month. Hash chain integrity: each event stores the SHA-256 of the previous event's hash.

## Key Conventions

- **BDPR format**: `BD-<2-char-state-code>-<7-digit-seq>` (validated by regex in `ProvenanceBase`).
- **All API responses** for sourced records must inherit from `ProvenanceBase` — enforces `source_department`, `source_system`, `source_as_of_date`, `data_freshness_status`.
- **Enums**: `DataFreshnessStatus` (LIVE/CACHED/SYNTHETIC), `RiskBand` (HIGH/MEDIUM/LOW/NEGLIGIBLE), `AccuracyClass` (A/B/C/D/UNKNOWN).
- **Structured logging**: use `structlog.get_logger()`, not the stdlib `logging` module, in services. Log `service=settings.service_name` on startup/shutdown.
- **No raw SQL in routers** — business logic and raw SQL belong in `services/` or `modules/` layers. Routers only marshal request/response.
- **Purpose-bound tokens**: sensitive endpoints (loan verification, legal use) require `require_purpose(["LOAN_VERIFICATION"])` dependency.
- **Geospatial**: use `ST_AsMVT` for tile generation, `ST_AsGeoJSON` for parcel geometry responses. All stored geometries are SRID 4326.
