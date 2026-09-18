Write-Host "Starting Bhoomi Dhrishti Frontend Apps..." -ForegroundColor Green
Write-Host ""

Write-Host "Stopping any existing frontend processes..." -ForegroundColor Gray
taskkill /F /IM node.exe 2>$null
Start-Sleep -Seconds 2

Write-Host "Starting Officer Console on port 3000..." -ForegroundColor Cyan
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd \"D:\Bhoomi Dhrishti\bhoomi-dhrishti\frontend\apps\officer\" && npx next dev -p 3000 > \"D:\Bhoomi Dhrishti\bhoomi-dhrishti\officer.log\" 2>&1" -WindowStyle Hidden

Write-Host "Starting Citizen Portal on port 3002..." -ForegroundColor Cyan
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd \"D:\Bhoomi Dhrishti\bhoomi-dhrishti\frontend\apps\citizen\" && npx next dev -p 3002 > \"D:\Bhoomi Dhrishti\bhoomi-dhrishti\citizen.log\" 2>&1" -WindowStyle Hidden

Write-Host "Starting Admin Console on port 3003..." -ForegroundColor Cyan
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd \"D:\Bhoomi Dhrishti\bhoomi-dhrishti\frontend\apps\admin\" && npx next dev -p 3003 > \"D:\Bhoomi Dhrishti\bhoomi-dhrishti\admin.log\" 2>&1" -WindowStyle Hidden

Write-Host ""
Write-Host "Waiting 45 seconds for apps to compile..." -ForegroundColor Gray
Start-Sleep -Seconds 45

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "Frontend Apps Started!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Officer Console:  http://localhost:3000" -ForegroundColor White
Write-Host "Citizen Portal:   http://localhost:3002" -ForegroundColor White
Write-Host "Admin Console:    http://localhost:3003" -ForegroundColor White
Write-Host ""
Write-Host "Logs:" -ForegroundColor Gray
Write-Host "  Officer: D:\Bhoomi Dhrishti\bhoomi-dhrishti\officer.log" -ForegroundColor Gray
Write-Host "  Citizen: D:\Bhoomi Dhrishti\bhoomi-dhrishti\citizen.log" -ForegroundColor Gray
Write-Host "  Admin:   D:\Bhoomi Dhrishti\bhoomi-dhrishti\admin.log" -ForegroundColor Gray
Write-Host ""
