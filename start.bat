@echo off
REM ──────────────────────────────────────────────────────────────
REM Stock Market Analysis Platform — Local Startup Script (Windows)
REM ──────────────────────────────────────────────────────────────

echo ============================================
echo   Stock Market Analysis Platform
echo   Starting local development servers...
echo ============================================
echo.

cd /d "%~dp0"

REM Create logs directory
if not exist "backend\logs" mkdir "backend\logs"

REM Backend setup
echo [1/4] Setting up Python virtual environment...
if not exist "backend\venv" (
    python -m venv backend\venv
)
call backend\venv\Scripts\activate.bat

echo [2/4] Installing Python dependencies...
pip install -q -r backend\requirements.txt

echo [3/4] Starting backend (FastAPI + Uvicorn)...
cd backend
start "Backend" cmd /c "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude venv --reload-exclude logs"
cd ..
echo        Backend URL: http://localhost:8000
echo        API Docs:    http://localhost:8000/docs
echo.

REM Frontend setup
echo [4/4] Installing frontend dependencies and starting Angular...
cd frontend
if not exist "node_modules" (
    npm install
)
start "Frontend" cmd /c "npx ng serve --host 0.0.0.0 --port 4200"
cd ..
echo        Frontend URL: http://localhost:4200
echo.

echo ============================================
echo   Both servers are running!
echo.
echo   Dashboard:  http://localhost:4200
echo   API Docs:   http://localhost:8000/docs
echo.
echo   Close this window to stop.
echo ============================================

REM Open browser
timeout /t 5 /nobreak >nul
start http://localhost:4200

pause
