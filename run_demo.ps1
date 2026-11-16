Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting AI ITSM Helpdesk Platform (SORIM.AI)" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

$backendDir = Join-Path $PSScriptRoot "backend"
$frontendDir = Join-Path $PSScriptRoot "frontend"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$backendDir'; python -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendDir'; npm run dev -- --port 3000"

Write-Host "Waiting 5 seconds for services to initialize..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

Write-Host "Opening http://localhost:3000 in your browser..." -ForegroundColor Green
Start-Process "http://localhost:3000"

Write-Host "Services started!" -ForegroundColor Green
Write-Host "Frontend:    http://localhost:3000" -ForegroundColor Yellow
Write-Host "Backend API: http://localhost:8000/docs" -ForegroundColor Yellow
