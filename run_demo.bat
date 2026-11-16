@echo off
echo ========================================================
echo   Starting AI ITSM Helpdesk Platform (SORIM.AI)
echo ========================================================
echo.
echo Starting FastAPI Backend on http://localhost:8000 ...
start "ITSM Backend" cmd /k "cd backend && python -m uvicorn app.main:app --reload --port 8000"

echo.
echo Starting React Frontend on http://localhost:3000 ...
start "ITSM Frontend" cmd /k "cd frontend && npm run dev -- --port 3000"

echo.
echo ========================================================
echo   Services Launched!
echo   Frontend: http://localhost:3000
echo   Backend API: http://localhost:8000/docs
echo ========================================================
