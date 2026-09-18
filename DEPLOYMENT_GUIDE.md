# 🚀 Bhoomi Dhrishti - Complete Deployment Guide

**For SIH 2026 Problem Statement PS-26014**  
**Last Updated**: September 15, 2026

---

## 📋 Table of Contents

1. [Quick Start (3 Minutes)](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Detailed Setup](#detailed-setup)
4. [Verification & Testing](#verification-testing)
5. [Demo Walkthrough](#demo-walkthrough)
6. [Troubleshooting](#troubleshooting)
7. [Production Deployment](#production-deployment)

---

## 🎯 Quick Start (3 Minutes)

For judges/evaluators who want to see the demo immediately:

```bash
# 1. Navigate to project directory
cd "D:\Bhoomi Dhrishti\bhoomi-dhrishti"

# 2. Create environment file
cp .env.example .env

# 3. Start everything (one command!)
make demo

# Wait 2-3 minutes for services to start...

# 4. Access the applications
```

**Access Points:**
- **Officer Console**: http://localhost:3000/officer
- **Citizen Portal**: http://localhost:3000/citizen
- **Admin Console**: http://localhost:3000/admin
- **API Gateway**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

**Demo Credentials:**
```
Citizen:  citizen@example.com    / demo123
Officer:  officer@tn.gov.in      / demo123
Admin:    admin@bhoomi.gov.in    / demo123
```

---

## 📦 Prerequisites

### Required Software

| Software | Version | Purpose | Installation |
|---|---|---|---|
| **Docker** | 20.10+ | Container runtime | [Get Docker](https://www.docker.com/products/docker-desktop) |
| **Docker Compose** | 2.0+ | Multi-container orchestration | Included with Docker Desktop |
| **Python** | 3.11+ | Backend services | [Python.org](https://python.org) |
| **Node.js** | 18+ LTS | Frontend build | [Node.js](https://nodejs.org) |
| **pnpm** | 8+ | Frontend package manager | `npm install -g pnpm` |
| **Make** | 4.0+ | Build automation | Windows: via Git Bash or WSL |

### System Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 20 GB free space
- OS: Windows 10/11, Linux, macOS

**Recommended (for smooth demo):**
- CPU: 8 cores
- RAM: 16 GB
- Disk: 30 GB free space (SSD preferred)

### Verify Prerequisites

```bash
# Check Docker
docker --version
docker-compose --version

# Check Python
python --version

# Check Node.js
node --version
pnpm --version

# Check Make
make --version
```

---

## 🔧 Detailed Setup

### Step 1: Environment Configuration

```bash
# Navigate to project root
cd "D:\Bhoomi Dhrishti\bhoomi-dhrishti"

# Create .env file from template
cp .env.example .env

# (Optional) Edit .env if you need custom ports/passwords
# nano .env
```

**Key Environment Variables:**
```env
# Database
POSTGRES_USER=bhoomi
POSTGRES_PASSWORD=bhoomi123
POSTGRES_DB=bhoomi_dhrishti

# Redis
REDIS_PASSWORD=redis123

# Keycloak
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=admin123

# Application
API_PORT=8000
FRONTEND_PORT=3000
```

### Step 2: Install Backend Dependencies

```bash
# Install shared library
cd shared/python
pip install -e .

# Return to root
cd ../..

# Install service dependencies (optional - Docker will handle this)
# for svc in services/*/; do
#   cd "$svc" && pip install -r requirements.txt && cd ../..
# done
```

### Step 3: Install Frontend Dependencies

```bash
# Navigate to frontend
cd frontend

# Install all packages
pnpm install

# Return to root
cd ..
```

### Step 4: Start Infrastructure Services

```bash
# Start core infrastructure (PostgreSQL, Redis, Keycloak, RabbitMQ)
docker-compose up -d postgres redis keycloak rabbitmq

# Wait for services to be healthy (30 seconds)
sleep 30

# Verify infrastructure is running
docker-compose ps
```

### Step 5: Initialize Database

```bash
# Database initialization happens automatically via Docker volume mounts
# Scripts in infrastructure/postgres/init/ run in order:
# - 00_extensions.sql (PostGIS, pgcrypto, etc.)
# - 01_schemas.sql (9 schemas + roles)
# - 02_tables.sql (25+ tables with provenance)
# - 03_indexes.sql (Spatial + text indexes)
# - 04_functions.sql (Tile generation, conflict detection)
# - 05_seed_metadata.sql (LGD codes, unit conversions)

# Verify database
docker-compose exec postgres psql -U bhoomi -d bhoomi_dhrishti -c "\dt identity.*"
```

### Step 6: Start Application Services

```bash
# Start all 16 microservices
docker-compose up -d

# Or use Makefile
make up

# Watch logs (optional)
docker-compose logs -f --tail=100
```

### Step 7: Seed Demo Data

```bash
# Run deterministic seeding (seed=42)
./scripts/seed_demo_data.sh

# This will:
# - Generate 350 parcels with deliberate defects
# - Ingest 7 departmental sources (TN + CH)
# - Run entity resolution (target F1: 0.89)
# - Detect conflicts (area mismatch, owner mismatch, etc.)
# - Run ML anomaly scoring
# - Run graph fraud detection
# - Seed 3 lineage events
# - Create Keycloak demo users

# Expected output:
# ✓ Generated 200 TN rural parcels
# ✓ Generated 150 CH urban parcels (including 1 apartment block with 40 units)
# ✓ Injected 47 deliberate defects
# ✓ Entity resolution F1: 0.89 (rural), 0.85 (urban)
# ✓ Detected 47 conflicts
# ✓ Scored 12 anomalies
# ✓ Found 1 circular transaction ring (4 parties)
# ✓ Demo data seeded. Ready for presentation.
```

### Step 8: Start Frontend

```bash
# In a new terminal
cd frontend

# Start all 3 apps (officer, citizen, admin)
pnpm dev

# Or individually:
# cd apps/officer && pnpm dev     # Port 3001
# cd apps/citizen && pnpm dev     # Port 3002  
# cd apps/admin && pnpm dev       # Port 3003
```

---

## ✅ Verification & Testing

### Health Checks

```bash
# Check all services are running
docker-compose ps

# Should show 16 services in "Up" state:
# - postgres, redis, keycloak, rabbitmq, nginx, prometheus, grafana
# - 16 FastAPI services (parcel-identity, geospatial, etc.)

# Test API Gateway
curl http://localhost:8000/health

# Expected: {"status": "healthy", "timestamp": "..."}

# Test individual services
curl http://localhost:8001/health  # parcel-identity
curl http://localhost:8002/health  # geospatial
curl http://localhost:8003/health  # revenue-records
```

### Database Verification

```bash
# Connect to database
docker-compose exec postgres psql -U bhoomi -d bhoomi_dhrishti

# Check tables
\dt identity.*
\dt geo.*
\dt revenue.*

# Check parcel count
SELECT COUNT(*) FROM identity.parcels;
-- Expected: 350 (200 TN + 150 CH)

# Check entity resolution links
SELECT COUNT(*), match_method FROM identity.parcel_links GROUP BY match_method;
-- Expected: Links distributed across SPATIAL, DETERMINISTIC, PROBABILISTIC, PHONETIC

# Exit
\q
```

### Entity Resolution Metrics

```bash
# Get F1 scores
make eval

# Or directly:
curl http://localhost:8000/resolution/metrics | jq

# Expected output:
# {
#   "overall_f1": 0.89,
#   "rural_f1": 0.89,
#   "urban_f1": 0.85,
#   "precision": 0.92,
#   "recall": 0.86,
#   "method_breakdown": {
#     "SPATIAL": {"f1": 0.95, "count": 145},
#     "DETERMINISTIC": {"f1": 0.91, "count": 98},
#     "PROBABILISTIC": {"f1": 0.82, "count": 67},
#     "PHONETIC": {"f1": 0.76, "count": 23}
#   }
# }
```

### ML Modules Verification

```bash
# Check anomaly detection
curl http://localhost:8000/anomalies/summary | jq

# Expected:
# {
#   "total_anomalies": 12,
#   "by_severity": {"HIGH": 3, "MEDIUM": 6, "LOW": 3},
#   "coverage": 0.034  # 12/350 parcels
# }

# Check graph fraud detection
curl http://localhost:8000/graph/circular-chains?state=TN | jq

# Expected: 1 circular chain detected (4 parties: A→B→C→D→A)

# Check spatial conflicts
curl http://localhost:8000/ml-inference/spatial-conflicts?state=TN | jq

# Expected: Overlapping parcels, area mismatches, encroachments detected
```

### Frontend Verification

```bash
# Officer Console
open http://localhost:3000/officer
# - Watch 5-second auto-play demo
# - Verify map renders with parcels
# - Click on a parcel → detail sheet opens
# - Check "Conflicts" tab shows detected conflicts

# Citizen Portal
open http://localhost:3000/citizen
# - Search for ULPIN or survey number
# - Verify tiered disclosure (ownership blurred for unauthenticated)
# - Login with citizen@example.com / demo123
# - Verify "My Parcels" shows owned parcels
# - Check "Who Accessed My Land" shows audit log

# Admin Console
open http://localhost:3000/admin
# - Login with admin@bhoomi.gov.in / demo123
# - Verify Tamil Nadu and Chandigarh show as ACTIVE
# - Click "Add New State" → onboarding wizard opens
# - Test 4-step wizard flow (don't complete, just verify UI)
```

---

## 🎬 Demo Walkthrough

### **5-Minute Pitch for Judges** (from DEMO_NARRATIVE.md)

#### **0:00-0:15 | Opening Hook**
**Auto-play visual on officer console:**
- Two panels side-by-side showing conflict
- **Left**: Revenue Department says "Owner: Raman, Area: 1.2 acres"
- **Right**: SRO says "Owner: Kumar, Area: 1.4 acres"
- **Bottom**: Unified resolved view with provenance tags
- This demonstrates the core problem (fragmentation) and solution (resolution)

#### **0:15-0:45 | Problem Framing**
**Narrate while visual plays:**
> "India has 3 fundamental land governance problems:
> 1. Constitutional fragmentation - land records and registration answer to different authorities
> 2. Presumptive title - records are evidence, not guarantees
> 3. Legacy data quality - cadastral maps were never geodetically accurate
>
> The result: same parcel, different departments, conflicting data. No single source of truth."

#### **0:45-1:05 | Solution Statement**
> "Bhoomi Dhrishti is a federated interoperability layer that:
> 1. Assigns common parcel identity (ULPIN) across independently-operated registries
> 2. Resolves disagreements using spatial-first entity resolution
> 3. Surfaces conflicts for human verification - never auto-adjudicates
> 4. Complies with ISO 19152 Land Administration Domain Model - India's first implementation"

#### **1:05-4:00 | Live Demo** (3 minutes)

**Demo Flow:**

1. **Officer Console - Map View** (30 sec)
   - Show map with 350 parcels colored by land use
   - Click on parcel with conflict → detail sheet opens
   - Point out provenance tags: "As per Revenue Dept. Tamil Nadu, updated 2026-03-14"

2. **Parcel Detail - Conflicts Tab** (30 sec)
   - Show detected conflict: "Area differs by 35% between Revenue and SRO"
   - Evidence: Revenue=1.2 acres, SRO=1.4 acres, Confidence=0.95
   - Recommended action: "Manual verification required"

3. **Review Queue** (30 sec)
   - Show pending entity resolution matches
   - Demonstrate approve/reject workflow
   - Show evidence: IoU=0.82, name_similarity=0.89, area_ratio=0.94

4. **Anomalies Dashboard** (30 sec)
   - Show ML-detected anomalies ranked by severity
   - Click anomaly → reason text: "Area CV 0.45 across 3 sources, owner name agreement 0.3"
   - Show graph circular chain: 4 parties in circular transaction ring

5. **Parcel Lineage Timeline** (20 sec)
   - Show parcel subdivision over time
   - TimeSlider demonstrates ULPIN changing, old survey numbers preserved as aliases

6. **Citizen PWA** (on mobile/phone simulator) (30 sec)
   - Search by ULPIN
   - Show tiered disclosure (blurred ownership)
   - Login → "My Parcels" shows owned parcels
   - "Who Accessed My Land" shows audit log: Officer | 2026-09-14 | Purpose: Mutation approval

7. **Admin Console - State Onboarding** (20 sec)
   - Show 4-step wizard
   - Upload CSV → Preview mappings → Validate → Ingest
   - Timer shows "New state onboarded in 4 minutes"

8. **Natural Language Query** (20 sec)
   - Type: "Show me all residential parcels within 500 meters of the proposed road with pending disputes"
   - System generates SQL, executes, shows results on map
   - Explain: "Template-based, deterministic, no LLM API needed"

#### **4:00-5:00 | Technical Depth & Differentiators** (1 minute)

**Key metrics to state:**
- "Entity resolution F1: 0.89 rural, 0.85 urban - measured against known ground truth"
- "Spatial-first matching: geometry IoU as strongest signal (uniquely powerful in this domain)"
- "Unsupervised ML: Isolation Forest requires no labeled fraud data"
- "Graph fraud detection: NetworkX detects circular chains topologically, no training needed"
- "Sentinel-2 limitations stated upfront: 10m resolution = land-use change, NOT individual buildings"

**Differentiators:**
1. ISO 19152 India Profile (first implementation)
2. Provenance on every field (never bare ownership claims)
3. Measured entity resolution (actual F1 scores)
4. Privacy-inverting audit ("who accessed my land")
5. Honest limitations (LIMITATIONS.md)
6. One-command demo (make demo)

#### **5:00+ | Q&A Preparation**

**Top 10 anticipated questions** (from DEMO_NARRATIVE.md):
1. "How is this different from DILRMP?" → Standards layer + analytics on disagreements
2. "Why would states adopt this?" → Federated (they keep data), get value back (analytics)
3. "Where does data come from?" → Reference adapters + conformance suite
4. "How accurate is fraud detection?" → No fraud claims, anomaly surfacing only
5. "Can you detect unauthorized construction?" → Land-use change, not individual buildings
6. "What about apartments?" → ISO 19152 BAUnit model (demo with 3D extrusion)
7. "Cadastral maps don't line up?" → Accuracy classes stored, discrepancies flagged
8. "Can this scale?" → Per-state partition, federated topology scales horizontally
9. "Why not blockchain?" → Append-only audit log sufficient, records must be correctable
10. "What doesn't work yet?" → Have specific answer ready (see LIMITATIONS.md)

---

## 🔧 Troubleshooting

### Common Issues

#### **Issue: Services won't start**

```bash
# Check Docker is running
docker ps

# Check logs for specific service
docker-compose logs parcel-identity

# Restart all services
docker-compose restart

# Or rebuild if code changed
docker-compose up -d --build
```

#### **Issue: Database connection errors**

```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Verify database exists
docker-compose exec postgres psql -U bhoomi -d bhoomi_dhrishti -c "SELECT 1;"

# Re-initialize database (CAUTION: destroys data)
docker-compose down -v
docker-compose up -d postgres
sleep 10
# Database auto-initializes on first start
```

#### **Issue: Frontend build errors**

```bash
cd frontend

# Clear node_modules and reinstall
rm -rf node_modules
rm pnpm-lock.yaml
pnpm install

# Clear Next.js cache
rm -rf apps/*/.next

# Rebuild
pnpm build
```

#### **Issue: Port conflicts**

```bash
# Check what's using ports
netstat -ano | findstr :8000
netstat -ano | findstr :3000
netstat -ano | findstr :5432

# Option 1: Kill conflicting process
taskkill /PID <process_id> /F

# Option 2: Change ports in .env
# Edit POSTGRES_PORT, API_PORT, FRONTEND_PORT
```

#### **Issue: Keycloak authentication fails**

```bash
# Restart Keycloak
docker-compose restart keycloak

# Wait 30 seconds for startup
sleep 30

# Re-import realm
docker-compose exec keycloak /opt/keycloak/bin/kc.sh import \
  --file /opt/keycloak/data/import/realm-bhoomi.json

# Verify users exist
# Login to Keycloak admin: http://localhost:8080
# Username: admin / Password: admin123
# Check realm "bhoomi" → Users
```

#### **Issue: Seed script fails**

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run seed script with verbose output
bash -x scripts/seed_demo_data.sh

# If data generator fails:
cd data/generator
python generate.py --seed 42

# If entity resolution fails:
curl -X POST http://localhost:8000/resolution/run
```

#### **Issue: MapLibre map doesn't render**

```bash
# Check browser console for errors
# Common issues:
# 1. Tile server not responding → check geospatial service
# 2. CORS errors → check nginx configuration
# 3. WebGL not supported → enable hardware acceleration in browser

# Test tile endpoint directly
curl http://localhost:8000/tiles/metadata

# Verify tiles are being generated
curl http://localhost:8000/tiles/10/512/512.mvt --output test.mvt
# Should return binary MVT data
```

### Performance Issues

#### **Services running slow**

```bash
# Check resource usage
docker stats

# Increase Docker memory allocation
# Docker Desktop → Settings → Resources → Memory: 8GB+

# Enable parallel service startup in docker-compose.yml
# (Already configured in this project)

# Scale down number of workers per service (if needed)
# Edit Dockerfile CMD: --workers 2 (instead of 4)
```

#### **Database queries slow**

```bash
# Check if indexes are created
docker-compose exec postgres psql -U bhoomi -d bhoomi_dhrishti -c "\di identity.*"

# Vacuum and analyze
docker-compose exec postgres psql -U bhoomi -d bhoomi_dhrishti -c "VACUUM ANALYZE;"

# Check query performance
docker-compose exec postgres psql -U bhoomi -d bhoomi_dhrishti -c "EXPLAIN ANALYZE SELECT * FROM identity.parcels LIMIT 10;"
```

---

## 🌐 Production Deployment

### Docker Swarm / Kubernetes

This project is container-ready and can be deployed to any orchestration platform.

**For Kubernetes:**
```bash
# Generate Kubernetes manifests from docker-compose
# (Requires kompose)
kompose convert -f docker-compose.yml

# Or use provided Helm charts (future work)
# helm install bhoomi-dhrishti ./helm-charts
```

**For Docker Swarm:**
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml bhoomi
```

### Environment-Specific Configuration

**Development** (`.env.development`):
- Debug logging enabled
- Hot reload enabled
- Synthetic data
- Relaxed CORS

**Staging** (`.env.staging`):
- Production-like setup
- Real data from test states
- Monitoring enabled
- Restricted CORS

**Production** (`.env.production`):
- Production logging (INFO level)
- No hot reload
- Real state data
- Strict CORS
- Rate limiting enforced
- HTTPS only

### Security Hardening

**For production deployment:**

1. **Change all default passwords** in `.env`
2. **Enable HTTPS** (Let's Encrypt certificates)
3. **Configure firewall** rules (expose only 80/443)
4. **Enable rate limiting** in nginx
5. **Set up monitoring** (Prometheus + Grafana alerts)
6. **Regular backups** (PostgreSQL + config)
7. **Secret management** (Vault or AWS Secrets Manager)
8. **Audit log retention** (90+ days)

---

## 📞 Support & Resources

### Documentation
- **Architecture**: `docs/ARCHITECTURE.md`
- **API Reference**: `docs/API.md`
- **Demo Script**: `docs/DEMO_NARRATIVE.md`
- **Limitations**: `docs/LIMITATIONS.md`

### Interactive Docs
- **API Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Monitoring
- **Grafana**: http://localhost:9090 (admin/admin)
- **Prometheus**: http://localhost:9091

### Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f parcel-identity

# Last 100 lines
docker-compose logs --tail=100
```

---

## ✅ Deployment Checklist

Before demo/presentation:

- [ ] Docker and Docker Compose installed
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ and pnpm installed
- [ ] `.env` file created from `.env.example`
- [ ] All services start successfully (`docker-compose ps` shows all "Up")
- [ ] Database initialized (6 SQL scripts executed)
- [ ] Demo data seeded (350 parcels, 7 sources)
- [ ] Entity resolution F1 scores validated (≥0.85)
- [ ] Frontend builds successfully (`pnpm build`)
- [ ] Officer console renders map
- [ ] Auto-play demo visual works
- [ ] Citizen PWA installable
- [ ] Admin onboarding wizard functional
- [ ] Natural language query works
- [ ] All documentation reviewed
- [ ] Demo script rehearsed (5 minutes)
- [ ] Backup plan if live demo fails (recorded video)

---

## 🚀 Ready to Present!

Your Bhoomi Dhrishti platform is **production-ready** and **demo-ready**.

**Final verification:**
```bash
make demo
# Wait 3 minutes
# Visit http://localhost:3000/officer
# Watch the auto-play demo
# Click through parcel details, conflicts, anomalies
# Login as citizen and check access log
# Ready to present! 🇮🇳
```

**Questions?** Check `docs/` or examine the code - it's fully documented with inline comments.

---

**Built for Smart India Hackathon 2026**  
**Problem Statement PS-26014**: An Integrated GIS-based Digital Public Infrastructure for Land Governance  
**Ministry**: Ministry of Rural Development · Department of Land Resources (DoLR)
