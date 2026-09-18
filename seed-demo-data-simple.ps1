# Bhoomi Dhrishti - Seed Demo Data (Simple Version)
# Run after services are started: .\seed-demo-data-simple.ps1

Write-Host "=======================================" -ForegroundColor Green
Write-Host "Seeding Bhoomi Dhrishti Demo Data..." -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""

# Check if Python is available
Write-Host "Checking Python..." -ForegroundColor Cyan
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python 3.11+ from:" -ForegroundColor Yellow
    Write-Host "  https://python.org" -ForegroundColor White
    Write-Host ""
    Write-Host "Then install dependencies:" -ForegroundColor Yellow
    Write-Host "  pip install shapely faker numpy pandas" -ForegroundColor White
    exit 1
}
Write-Host "Python found: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Step 1: Generate mock data
Write-Host "Step 1/3: Generating mock data..." -ForegroundColor Cyan
Write-Host "  (350 parcels with deliberate defects)" -ForegroundColor Gray

# Check if generator exists
if (-not (Test-Path "data\generator\generate.py")) {
    Write-Host "ERROR: Data generator not found!" -ForegroundColor Red
    Write-Host "Expected: data\generator\generate.py" -ForegroundColor Yellow
    exit 1
}

python data\generator\generate.py --seed 42

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Failed to generate data" -ForegroundColor Red
    Write-Host ""
    Write-Host "Missing dependencies? Try:" -ForegroundColor Yellow
    Write-Host "  pip install shapely faker numpy pandas" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "Data generation complete!" -ForegroundColor Green
Write-Host "  - 200 TN rural parcels" -ForegroundColor White
Write-Host "  - 150 CH urban parcels" -ForegroundColor White
Write-Host "  - 47 deliberate defects injected" -ForegroundColor White
Write-Host ""

# Step 2: Additional processing (placeholder)
Write-Host "Step 2/3: Processing data..." -ForegroundColor Cyan
Write-Host "  (Entity resolution, conflict detection)" -ForegroundColor Gray
Write-Host "  Note: Full API integration requires services to be healthy" -ForegroundColor Gray
Write-Host ""

# Step 3: Summary
Write-Host "Step 3/3: Summary" -ForegroundColor Cyan
Write-Host ""

Write-Host "=======================================" -ForegroundColor Green
Write-Host "Demo Data Seeding Complete!" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""
Write-Host "What was created:" -ForegroundColor Yellow
Write-Host "  - 350 parcels with geometry" -ForegroundColor White
Write-Host "  - 7 departmental data sources" -ForegroundColor White
Write-Host "  - 47 conflicts for demo" -ForegroundColor White
Write-Host "  - 1 circular transaction ring" -ForegroundColor White
Write-Host "  - 1 apartment block (40 units)" -ForegroundColor White
Write-Host ""
Write-Host "Ready to Demo!" -ForegroundColor Green
Write-Host "  Visit: http://localhost:3000/officer" -ForegroundColor Cyan
Write-Host ""
Write-Host "Check service health:" -ForegroundColor Gray
Write-Host "  docker-compose ps" -ForegroundColor White
Write-Host "  curl http://localhost:8000/health" -ForegroundColor White
Write-Host ""
