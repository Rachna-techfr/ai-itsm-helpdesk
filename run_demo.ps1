Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting AI ITSM Helpdesk Platform (SORIM.AI)" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "Services started!" -ForegroundColor Green
Write-Host "Frontend:    http://localhost:5173" -ForegroundColor Yellow
Write-Host "Backend API: http://localhost:8000/docs" -ForegroundColor Yellow
