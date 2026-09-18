#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Bhoomi Dhrishti – One-Command Demo Startup
# Starts all services, waits for health checks, and seeds demo data
# ─────────────────────────────────────────────────────────────────────────────

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "🚀 Starting Bhoomi Dhrishti Demo..."
echo "   Project root: $PROJECT_ROOT"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Environment check
# ─────────────────────────────────────────────────────────────────────────────
echo "📋 Checking environment..."

if [ ! -f .env ]; then
    echo "⚠ .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "❗ Please edit .env and set proper passwords before production use!"
    echo ""
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker and try again."
    exit 1
fi

# Check for Docker Compose
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose and try again."
    exit 1
fi

echo "✓ Environment ready"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Start infrastructure services
# ─────────────────────────────────────────────────────────────────────────────
echo "🏗️  Step 1/5: Starting infrastructure services..."
docker compose up -d postgres redis keycloak rabbitmq

echo "   Waiting for infrastructure to be ready..."
sleep 15  # Give databases time to initialize

echo "✓ Infrastructure services started"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 3: Start application services
# ─────────────────────────────────────────────────────────────────────────────
echo "📦 Step 2/5: Starting application services..."
docker compose up -d --build

echo "✓ Application services started"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 4: Wait for health checks
# ─────────────────────────────────────────────────────────────────────────────
echo "🏥 Step 3/5: Waiting for services to be healthy..."

if [ -f "$SCRIPT_DIR/wait-for-services.sh" ]; then
    bash "$SCRIPT_DIR/wait-for-services.sh"
else
    echo "   (wait-for-services.sh not found, using fixed delay)"
    sleep 30
fi

echo "✓ Services are healthy"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 5: Seed demo data
# ─────────────────────────────────────────────────────────────────────────────
echo "🌱 Step 4/5: Seeding demo data..."

if [ -f "$SCRIPT_DIR/seed_demo_data.sh" ]; then
    bash "$SCRIPT_DIR/seed_demo_data.sh"
else
    echo "⚠ seed_demo_data.sh not found, skipping data seeding"
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────────
# Step 6: Display status
# ─────────────────────────────────────────────────────────────────────────────
echo "📊 Step 5/5: Checking service status..."
docker compose ps

echo ""
echo "══════════════════════════════════════════════════════════════════════════"
echo "✓ Bhoomi Dhrishti is running!"
echo "══════════════════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Access Points:"
echo "   ├─ Officer Console:    http://localhost:3000/officer"
echo "   ├─ Citizen Portal:     http://localhost:3000/citizen"
echo "   ├─ Admin Dashboard:    http://localhost:3000/admin"
echo "   ├─ API Gateway:        http://localhost:8000"
echo "   ├─ API Docs:           http://localhost:8000/docs"
echo "   ├─ Keycloak:           http://localhost:8080"
echo "   ├─ Grafana:            http://localhost:3001"
echo "   └─ Prometheus:         http://localhost:9090"
echo ""
echo "👥 Demo Credentials:"
echo "   ├─ Citizen:  citizen@example.com   / demo123"
echo "   ├─ Officer:  officer@tn.gov.in     / demo123"
echo "   └─ Admin:    admin@bhoomi.gov.in   / demo123"
echo ""
echo "📚 Quick Commands:"
echo "   make logs          - Tail all service logs"
echo "   make logs-<svc>    - Tail specific service logs"
echo "   make ps            - Show running containers"
echo "   make down          - Stop all services"
echo ""
echo "Happy hacking! 🎉"
echo ""
