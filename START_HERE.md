# 🚀 START HERE - Bhoomi Dhrishti Quick Launch

## ⚠️ IMPORTANT: Prerequisites

### 1. Start Docker Desktop FIRST

**Before running anything, you MUST start Docker Desktop:**

1. **Open Docker Desktop** from Windows Start Menu
2. **Wait** for Docker to fully start (whale icon in system tray)
3. Verify it's running: The Docker Desktop window shows "Engine running"

**If Docker Desktop is not installed:**
- Download from: https://www.docker.com/products/docker-desktop
- Install and restart your computer
- Open Docker Desktop and wait for it to start

---

## 🎯 Quick Start (After Docker is Running)

### Option 1: PowerShell Script (Recommended)

```powershell
# In PowerShell (run as yourself, NOT as admin)
cd "D:\Bhoomi Dhrishti\bhoomi-dhrishti"

# Start all services
.\start-demo.ps1

# Wait 2-3 minutes, then seed data
.\seed-demo-data.ps1
```

### Option 2: Manual Docker Compose

```powershell
# In PowerShell
cd "D:\Bhoomi Dhrishti\bhoomi-dhrishti"

# 1. Start infrastructure
docker-compose up -d postgres redis keycloak rabbitmq

# 2. Wait 30 seconds
Start-Sleep -Seconds 30

# 3. Start all services
docker-compose up -d

# 4. Check status
docker-compose ps

# 5. Watch logs (optional)
docker-compose logs -f
```

---

## ✅ Verify Services Are Running

```powershell
# Check all services
docker-compose ps

# Expected: All services show "Up" status
# - postgres, redis, keycloak, rabbitmq
# - parcel-identity, geospatial, revenue-records
# - (and 13 more services)

# Check API health
curl http://localhost:8000/health

# Expected: {"status": "healthy"}
```

---

## 🌱 Seed Demo Data

After services are running:

```powershell
# Generate mock data
python data/generator/generate.py --seed 42

# Expected output:
# ✓ Generated 200 TN rural parcels
# ✓ Generated 150 CH urban parcels
# ✓ Injected 47 deliberate defects
```

**If Python not found:**
```powershell
# Install Python 3.11+ from python.org
# Then install dependencies:
pip install shapely faker numpy pandas
```

---

## 🌐 Access the Applications

Once services are running:

| Application | URL |
|---|---|
| **Officer Console** | http://localhost:3000/officer |
| **Citizen Portal** | http://localhost:3000/citizen |
| **Admin Console** | http://localhost:3000/admin |
| **API Gateway** | http://localhost:8000 |
| **API Documentation** | http://localhost:8000/docs |
| **Grafana** | http://localhost:9090 |

**Demo Credentials:**
```
Citizen:  citizen@example.com    / demo123
Officer:  officer@tn.gov.in      / demo123
Admin:    admin@bhoomi.gov.in    / demo123
```

---

## 🐛 Troubleshooting

### "Docker daemon not running"
→ **Start Docker Desktop** from Windows Start Menu, wait for it to fully start

### "Port already in use"
```powershell
# Find what's using the port (e.g., 8000)
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <process_id> /F
```

### "Services won't start"
```powershell
# Stop all services
docker-compose down

# Remove volumes (CAUTION: deletes data)
docker-compose down -v

# Start fresh
docker-compose up -d
```

### "Database connection errors"
```powershell
# Check PostgreSQL is running
docker-compose ps postgres

# View logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### "Frontend not loading"
```powershell
# Install frontend dependencies
cd frontend
pnpm install

# Start frontend (separate terminal)
pnpm dev

# Or build production version
pnpm build
pnpm start
```

---

## 📊 Expected Startup Time

- **Infrastructure** (postgres, redis, keycloak, rabbitmq): 30-60 seconds
- **All 16 services**: 60-90 seconds
- **Total ready time**: ~3-4 minutes

---

## 🔍 Check Service Health

```powershell
# Individual service health checks
curl http://localhost:8001/health  # parcel-identity
curl http://localhost:8002/health  # geospatial
curl http://localhost:8003/health  # revenue-records
curl http://localhost:8004/health  # registration
curl http://localhost:8008/health  # trust-engine
curl http://localhost:8009/health  # ml-inference

# All should return: {"status": "healthy"}
```

---

## 📝 Startup Checklist

- [ ] Docker Desktop is running (check system tray)
- [ ] Navigated to project directory
- [ ] Created .env file (`cp .env.example .env`)
- [ ] Started infrastructure services
- [ ] Waited 30 seconds
- [ ] Started all services
- [ ] Checked `docker-compose ps` shows all "Up"
- [ ] Generated demo data
- [ ] Accessed http://localhost:3000/officer
- [ ] Ready to demo! 🎉

---

## 🚀 Full Command Sequence (Copy-Paste)

```powershell
# Make sure Docker Desktop is running first!

cd "D:\Bhoomi Dhrishti\bhoomi-dhrishti"

# Start infrastructure
docker-compose up -d postgres redis keycloak rabbitmq

# Wait
Start-Sleep -Seconds 30

# Start all services
docker-compose up -d

# Wait
Start-Sleep -Seconds 60

# Check status
docker-compose ps

# Generate data
python data/generator/generate.py --seed 42

# Access officer console
Start-Process "http://localhost:3000/officer"
```

---

## 📚 Next Steps After Startup

1. **Visit Officer Console**: http://localhost:3000/officer
   - Watch the 5-second auto-play conflict demo
   - Click on a parcel to see details

2. **Read Demo Guide**: `QUICK_START.md`
   - 5-minute demo flow
   - Key metrics to state
   - Judge Q&A preparation

3. **Full Documentation**: `DEPLOYMENT_GUIDE.md`
   - Complete setup guide
   - Troubleshooting
   - Production deployment

---

## 🛑 Stop All Services

```powershell
# Stop services (keeps data)
docker-compose down

# Stop and remove data (fresh start next time)
docker-compose down -v
```

---

## ❓ Need Help?

**Full guides in this directory:**
- `DEPLOYMENT_GUIDE.md` - Complete 12,000-word guide
- `QUICK_START.md` - 3-minute quick reference
- `BUILD_COMPLETE.md` - Full project summary
- `docs/DEMO_NARRATIVE.md` - 5-minute pitch script

**Common issues:**
- Docker not running → Start Docker Desktop
- Port conflicts → Kill conflicting process or change ports in .env
- Services unhealthy → Check logs: `docker-compose logs [service]`

---

**You're almost there! Just start Docker Desktop and run the commands above.** 🚀
