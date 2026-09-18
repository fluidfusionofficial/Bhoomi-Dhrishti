# Bhoomi Dhrishti - Demo Startup Script (Simple Version)
# Run with: .\start-demo-simple.ps1

Write-Host "=======================================" -ForegroundColor Green
Write-Host "Starting Bhoomi Dhrishti Demo..." -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""

# Check if Docker is running
Write-Host "Checking Docker..." -ForegroundColor Cyan
$dockerRunning = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Steps:" -ForegroundColor Yellow
    Write-Host "1. Open Docker Desktop from Windows Start Menu" -ForegroundColor White
    Write-Host "2. Wait for 'Engine running' message" -ForegroundColor White
    Write-Host "3. Run this script again" -ForegroundColor White
    exit 1
}
Write-Host "Docker is running!" -ForegroundColor Green
Write-Host ""

# Step 1: Start infrastructure services
Write-Host "Step 1/5: Starting infrastructure..." -ForegroundColor Cyan
Write-Host "  (PostgreSQL, Redis, Keycloak, RabbitMQ)" -ForegroundColor Gray
docker-compose up -d postgres redis keycloak rabbitmq

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to start infrastructure services" -ForegroundColor Red
    exit 1
}
Write-Host "Infrastructure services starting..." -ForegroundColor Green
Write-Host ""

# Step 2: Wait for infrastructure
Write-Host "Step 2/5: Waiting for infrastructure (30 seconds)..." -ForegroundColor Cyan
Start-Sleep -Seconds 30
Write-Host "Infrastructure should be ready" -ForegroundColor Green
Write-Host ""

# Step 3: Start all application services
Write-Host "Step 3/5: Starting all 16 microservices..." -ForegroundColor Cyan
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to start application services" -ForegroundColor Red
    exit 1
}
Write-Host "All services starting..." -ForegroundColor Green
Write-Host ""

# Step 4: Wait for services to be healthy
Write-Host "Step 4/5: Waiting for services to be healthy (60 seconds)..." -ForegroundColor Cyan
Start-Sleep -Seconds 60
Write-Host "Services should be ready" -ForegroundColor Green
Write-Host ""

# Start frontend apps
Write-Host "Starting Officer Console (port 3000)..." -ForegroundColor Cyan
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd D:\\Bhoomi Dhrishti\\bhoomi-dhrishti\\frontend\\apps\\officer && npx next dev -p 3000 > D:\\Bhoomi Dhrishti\\bhoomi-dhrishti\\officer.log 2>&1" -WindowStyle Hidden
Write-Host "Starting Citizen Portal (port 3002)..." -ForegroundColor Cyan
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd D:\\Bhoomi Dhrishti\\bhoomi-dhrishti\\frontend\\apps\\citizen && npx next dev -p 3002 > D:\\Bhoomi Dhrishti\\bhoomi-dhrishti\\citizen.log 2>&1" -WindowStyle Hidden
Write-Host "Starting Admin Console (port 3003)..." -ForegroundColor Cyan
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd D:\\Bhoomi Dhrishti\\bhoomi-dhrishti\\frontend\\apps\\admin && npx next dev -p 3003 > D:\\Bhoomi Dhrishti\\bhoomi-dhrishti\\admin.log 2>&1" -WindowStyle Hidden
Write-Host "Waiting 30 seconds for frontend apps to start..." -ForegroundColor Gray
Start-Sleep -Seconds 30
Write-Host ""

# Step 5: Check service status
Write-Host "Step 5/5: Checking service status..." -ForegroundColor Cyan
docker-compose ps
Write-Host ""

Write-Host "=======================================" -ForegroundColor Green
Write-Host "Bhoomi Dhrishti Demo is Ready!" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access Points:" -ForegroundColor Yellow
Write-Host "  Officer Console:  http://localhost:3000/officer" -ForegroundColor White
Write-Host "  Citizen Portal:   http://localhost:3000/citizen" -ForegroundColor White
Write-Host "  Admin Console:    http://localhost:3000/admin" -ForegroundColor White
Write-Host "  API Gateway:      http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:         http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Demo Credentials:" -ForegroundColor Yellow
Write-Host "  Citizen:  citizen@example.com / demo123" -ForegroundColor White
Write-Host "  Officer:  officer@tn.gov.in / demo123" -ForegroundColor White
Write-Host "  Admin:    admin@bhoomi.gov.in / demo123" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Run: .\seed-demo-data-simple.ps1" -ForegroundColor White
Write-Host "  2. Visit: http://localhost:3000/officer" -ForegroundColor White
Write-Host ""
Write-Host "To view logs: docker-compose logs -f" -ForegroundColor Gray
Write-Host "To stop: docker-compose down" -ForegroundColor Gray
Write-Host ""
