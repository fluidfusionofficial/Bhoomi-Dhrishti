# Bhoomi Dhrishti

**Federated Land Governance Interoperability Platform**

SIH 2026 | Problem Statement PS-26014 | Ministry of Rural Development / DoLR

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL: 16](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://postgresql.org)
[![PostGIS: 3.4](https://img.shields.io/badge/PostGIS-3.4-blue.svg)](https://postgis.net)

---

## Overview

Bhoomi Dhrishti is a **federated land-records interoperability platform** that addresses the critical problem of fragmented land records across Indian states and departments. Built on **ISO 19152 (LADM) India Profile**, the system creates a parcel-centric identity fabric that links disparate departmental sources without requiring centralized data migration.

### The Problem

Indian land governance operates under **presumptive title** (ULPIN Act 2008), where ownership is evidenced by Revenue records (RoR), Registration documents, and tax assessments — none of which constitute absolute title. Constitutional fragmentation distributes land records across:
- Revenue Department (RoR, survey records)
- Registration Department (sale deeds, mortgages)
- Urban Local Bodies (property tax, building permissions)
- Planning authorities (zoning, land-use)
- Courts (dispute adjudication)

**Result**: 35% area mismatches, ownership disputes, unauthorized constructions.

### Our Solution

- ✅ **Federated interoperability** — Links departmental sources, no forced data migration
- ✅ **ISO 19152 LADM India Profile** — International standard implementation
- ✅ **Spatial-first entity resolution** — F1 0.89 rural, 0.85 urban (measured)
- ✅ **Provenance on every field** — Full audit trail with source tracking
- ✅ **Unsupervised ML** — Anomaly detection + graph fraud detection
- ✅ **Privacy inversion** — "Who accessed my land" citizen-facing
- ✅ **Honest limitations** — See [LIMITATIONS.md](docs/LIMITATIONS.md)

---

## Quick Start

### One-Command Demo

```bash
make demo
```

This will:
1. Start all 16 microservices + infrastructure (PostgreSQL, Redis, Keycloak, RabbitMQ)
2. Wait for health checks
3. Seed demo data (Tamil Nadu rural + Chandigarh urban)
4. Create demo user accounts

**Access the platform at**:
- **Officer Console**: http://localhost:3000/officer
- **Citizen Portal**: http://localhost:3000/citizen
- **Admin Dashboard**: http://localhost:3000/admin
- **API Gateway**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Keycloak**: http://localhost:8080
- **Grafana**: http://localhost:3001

**Demo Credentials**:
```
Citizen:  citizen@example.com   / demo123
Officer:  officer@tn.gov.in     / demo123
Admin:    admin@bhoomi.gov.in   / demo123
```

### Manual Setup

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env and set passwords

# 2. Start infrastructure
docker compose up -d postgres redis keycloak rabbitmq
sleep 15  # Wait for databases

# 3. Start all services
docker compose up -d --build

# 4. Seed demo data
make seed

# 5. Check status
make ps
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Bhoomi Dhrishti Platform                        │
│                                                                      │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │   Citizen PWA   │  │ Officer Console  │  │ Admin Dashboard  │  │
│  │  (Mobile-first) │  │   (Desktop)      │  │  (Monitoring)    │  │
│  └────────┬────────┘  └────────┬─────────┘  └────────┬─────────┘  │
│           │                    │                      │             │
│           └────────────────────┴──────────────────────┘             │
│                               │                                     │
│  ┌────────────────────────────▼──────────────────────────────────┐ │
│  │              API Gateway (NGINX + Auth)                       │ │
│  └────────────────────────────┬──────────────────────────────────┘ │
│                               │                                     │
│  ┌────────────────────────────▼──────────────────────────────────┐ │
│  │                   16 Microservices (FastAPI)                  │ │
│  │                                                                │ │
│  │  Parcel Identity  │  Geospatial    │  Revenue Records         │ │
│  │  Registration     │  Planning      │  Fiscal (Tax)            │ │
│  │  Trust Engine     │  ML Inference  │  Satellite Detection     │ │
│  │  Search           │  Analytics     │  Audit Trail             │ │
│  │  Notifications    │  Citizen API   │  Interoperability        │ │
│  │  Utilities        │                                            │ │
│  └────────────────────────────┬──────────────────────────────────┘ │
│                               │                                     │
│  ┌────────────────────────────▼──────────────────────────────────┐ │
│  │   Data Layer (PostgreSQL + PostGIS + Redis + RabbitMQ)       │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

**See detailed architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Key Features

### 1. End-to-End Workflows

Three complete cross-departmental workflows demonstrating platform capabilities:

**Property Sale Workflow** (`workflows/property_sale.py`)
- Pre-checks: encumbrances, disputes, ownership, area consistency, zoning
- SRO registration
- Mutation request to Revenue
- Tax assessment update to ULB
- Complete audit trail

**Building Permission Workflow** (`workflows/building_permission.py`)
- Automated screening: zoning, FSI/FAR, setbacks, tax dues
- Officer review queue
- Approval notifications

**Unauthorized Conversion Detection** (`workflows/unauthorized_conversion.py`)
- Satellite change detection (Sentinel-2)
- Cross-reference with building permissions
- Auto-generate enforcement cases
- Field officer assignment

### 2. Spatial-First Entity Resolution

Links parcels across departmental sources using:
- Geometry overlap (PostGIS ST_Intersects)
- Survey number matching
- Area variance checking
- Boundary topology analysis

**Measured Performance**:
- Rural F1 Score: **0.89**
- Urban F1 Score: **0.85**

### 3. ML Anomaly Detection

**Unsupervised learning** (no labeled fraud data):
- **Isolation Forest**: Price outliers, transaction frequency anomalies
- **Graph Analysis** (NetworkX): Circular ownership chains, dense clusters
- **Satellite**: Land-use change detection (10m resolution)

### 4. Privacy & Security

- **Aadhaar hashing**: SHA-256 (never stored in plaintext)
- **PII encryption**: AES-256-GCM with KMS
- **Tiered RBAC**: Citizen, Officer (jurisdiction-scoped), Admin
- **Privacy inversion**: Citizens see "Who accessed my land"
- **Audit trail**: Immutable, append-only

### 5. ISO 19152 Compliance

First Indian implementation of **Land Administration Domain Model (ISO 19152:2012)**:
- LA_Parcel (Spatial Unit)
- LA_Party (Rights Holder)
- LA_RRR (Rights, Restrictions, Responsibilities)
- LA_Source (Provenance)
- India Extensions: Mutation tracking, Parcel lineage

---

## Services

| Service               | Port | Responsibility                                     |
|-----------------------|------|----------------------------------------------------|
| `parcel-identity`     | 8001 | Canonical parcel model, entity resolution, lineage |
| `geospatial`          | 8002 | Spatial queries, overlay analysis, topology checks |
| `revenue-records`     | 8003 | RoR integration, mutation tracking                |
| `registration`        | 8004 | SRO deed integration, encumbrance certificates    |
| `planning-zoning`     | 8005 | Zoning, FSI/FAR, building permissions             |
| `fiscal`              | 8006 | Property tax, encumbrances, valuation             |
| `utilities`           | 8007 | Water body mapping, infrastructure               |
| `trust-engine`        | 8008 | Conflict detection, dispute tracking              |
| `ml-inference`        | 8009 | Anomaly scoring, fraud detection                  |
| `satellite`           | 8016 | Change detection, land-use classification         |
| `citizen-services`    | 8010 | Public-facing APIs, parcel search                 |
| `audit`               | 8011 | Immutable audit trail, compliance reporting       |
| `notifications`       | 8012 | Email/SMS alerts, workflow notifications          |
| `search`              | 8013 | Full-text search (PostgreSQL + tsvector)          |
| `analytics`           | 8014 | Dashboards, KPIs, conflict summaries              |
| `interoperability`    | 8015 | ETL pipelines, state onboarding, data mapping     |

**Interactive API Docs**: Each service exposes Swagger UI at `/docs`

---

## Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI (async ASGI)
- **Database**: PostgreSQL 16 + PostGIS 3.4
- **Cache**: Redis 7
- **Message Queue**: RabbitMQ 3
- **Auth**: Keycloak 24 (OIDC/OAuth2)

### ML & Analytics
- **ML**: scikit-learn (Isolation Forest), NetworkX (graph fraud)
- **Satellite**: Sentinel Hub API (Sentinel-2 10m resolution)
- **NLP**: spaCy (natural language search)

### Frontend
- **Framework**: React 18 + TypeScript
- **Maps**: Mapbox GL JS (vector tiles)
- **State**: Zustand + React Query
- **UI**: Tailwind CSS + shadcn/ui

### DevOps
- **Orchestration**: Docker Compose (demo), Kubernetes (production)
- **Monitoring**: Prometheus + Grafana
- **Logging**: Structured JSON (ELK/Loki-ready)

---

## Development

### Common Commands

```bash
make demo          # One-command demo startup
make seed          # Seed demo data
make eval          # Run entity resolution evaluation
make test-all      # Run all service tests
make logs          # Tail all service logs
make ps            # Show running containers
make clean         # Remove containers and volumes
make lint          # Run Python linting
```

### Running Workflows

```bash
# Property sale workflow
python workflows/property_sale.py request.json

# Building permission workflow
python workflows/building_permission.py request.json

# Unauthorized conversion detection
python workflows/unauthorized_conversion.py TN-TVL 90
```

### Service Development

```bash
# Watch logs for specific service
make logs-parcel-identity

# Restart a service
docker compose restart parcel-identity

# Run tests for a service
docker compose run --rm parcel-identity pytest tests/ -v

# Open database shell
make psql
```

---

## Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** — Federated topology, ISO 19152 India profile, entity resolution cascade
- **[API.md](docs/API.md)** — OpenAPI endpoints, authentication, rate limits
- **[DEMO_NARRATIVE.md](docs/DEMO_NARRATIVE.md)** — 5-minute pitch script for judges
- **[LIMITATIONS.md](docs/LIMITATIONS.md)** — Honest disclosure of constraints

---

## Demo Credentials

| Role     | Username                | Password | Access Level                          |
|----------|-------------------------|----------|---------------------------------------|
| Citizen  | citizen@example.com     | demo123  | Own parcel only                       |
| Officer  | officer@tn.gov.in       | demo123  | Tamil Nadu Tiruvannamalai district    |
| Admin    | admin@bhoomi.gov.in     | demo123  | System-wide access                    |

---

## Key Differentiators

1. **ISO 19152 Compliance** — First India implementation of LADM
2. **Federated Architecture** — No forced data migration
3. **Provenance on Every Field** — Full audit trail
4. **Measured Entity Resolution** — F1 scores published
5. **Privacy Inversion** — "Who accessed my land" citizen-facing
6. **Honest Limitations** — See [LIMITATIONS.md](docs/LIMITATIONS.md)

---

## Contributing

This is a demonstration project for SIH 2026. For production deployment, partnerships with state governments and NIC are required for:
- Data sharing agreements
- Schema mapping workshops
- Pilot district rollouts

---

## License

Government of India / Ministry of Rural Development. For evaluation under SIH 2026.

---

## Contact

For questions about this project, please refer to the [DEMO_NARRATIVE.md](docs/DEMO_NARRATIVE.md) for anticipated Q&A.

**Built with ❤️ for transparent, auditable land governance in India.**
