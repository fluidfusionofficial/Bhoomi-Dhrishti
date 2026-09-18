# Bhoomi Dhrishti - Demo Startup Script for Windows PowerShell
# Run with: .\start-demo.ps1

Write-Host "🚀 Starting Bhoomi Dhrishti Demo..." -ForegroundColor Green
Write-Host ""

# Step 1: Start infrastructure services
Write-Host "📦 Step 1/5: Starting infrastructure (PostgreSQL, Redis, Keycloak, RabbitMQ)..." -ForegroundColor Cyan
docker-compose up -d postgres redis keycloak rabbitmq

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start infrastructure services" -ForegroundColor Red
    exit 1
}

# Step 2: Wait for infrastructure to be ready
Write-Host ""
Write-Host "⏳ Step 2/5: Waiting for infrastructure to be ready (30 seconds)..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

# Step 3: Start all application services
Write-Host ""
Write-Host "🔧 Step 3/5: Starting all 16 microservices..." -ForegroundColor Cyan
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start application services" -ForegroundColor Red
    exit 1
}

# Step 4: Wait for services to be healthy
Write-Host ""
Write-Host "⏳ Step 4/5: Waiting for services to be healthy (45 seconds)..." -ForegroundColor Cyan
Start-Sleep -Seconds 45

# Step 5: Check service status
Write-Host ""
Write-Host "✅ Step 5/5: Checking service status..." -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "✨ Bhoomi Dhrishti Demo is Ready!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access Points:" -ForegroundColor Yellow
Write-Host "   Officer Console:  http://localhost:3000/officer" -ForegroundColor White
Write-Host "   Citizen Portal:   http://localhost:3000/citizen" -ForegroundColor White
Write-Host "   Admin Console:    http://localhost:3000/admin" -ForegroundColor White
Write-Host "   API Gateway:      http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs:         http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Grafana:          http://localhost:9090" -ForegroundColor White
Write-Host ""
Write-Host "🔑 Demo Credentials:" -ForegroundColor Yellow
Write-Host "   Citizen:  citizen@example.com    / demo123" -ForegroundColor White
Write-Host "   Officer:  officer@tn.gov.in      / demo123" -ForegroundColor White
Write-Host "   Admin:    admin@bhoomi.gov.in    / demo123" -ForegroundColor White
Write-Host ""
Write-Host "📊 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Wait 2 more minutes for all services to fully initialize" -ForegroundColor White
Write-Host "   2. Run seed script: .\seed-demo-data.ps1" -ForegroundColor White
Write-Host "   3. Visit: http://localhost:3000/officer" -ForegroundColor White
Write-Host ""
Write-Host "📚 Logs: docker-compose logs -f [service-name]" -ForegroundColor Gray
Write-Host "🛑 Stop: docker-compose down" -ForegroundColor Gray
Write-Host ""
