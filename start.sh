#!/bin/bash
# ──────────────────────────────────────────────────────────────
# Stock Market Analysis Platform — Local Startup Script (Linux/Mac)
# ──────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "  Stock Market Analysis Platform"
echo "  Starting local development servers..."
echo "============================================"
echo ""

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 is required but not found."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "ERROR: Node.js is required but not found."; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "ERROR: npm is required but not found."; exit 1; }

# Create logs directory
mkdir -p backend/logs

# Backend setup
echo "[1/4] Setting up Python virtual environment..."
if [ ! -d "backend/venv" ]; then
    python3 -m venv backend/venv
fi
source backend/venv/bin/activate

echo "[2/4] Installing Python dependencies..."
pip install -q -r backend/requirements.txt

echo "[3/4] Starting backend (FastAPI + Uvicorn)..."
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude "venv" --reload-exclude "logs" &
BACKEND_PID=$!
cd ..
echo "       Backend PID: $BACKEND_PID"
echo "       Backend URL: http://localhost:8000"
echo "       API Docs:    http://localhost:8000/docs"
echo ""

# Frontend setup
echo "[4/4] Installing frontend dependencies and starting Angular..."
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
npx ng serve --host 0.0.0.0 --port 4200 &
FRONTEND_PID=$!
cd ..
echo "       Frontend PID: $FRONTEND_PID"
echo "       Frontend URL: http://localhost:4200"
echo ""

echo "============================================"
echo "  Both servers are running!"
echo ""
echo "  Dashboard:  http://localhost:4200"
echo "  API Docs:   http://localhost:8000/docs"
echo ""
echo "  Press Ctrl+C to stop all servers."
echo "============================================"

# Trap Ctrl+C to kill both processes
trap "echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

# Wait for either process to exit
wait
