#!/usr/bin/env bash
set -e

echo "=== AI Phishing Demo — Startup ==="
echo ""

# ── Backend ──────────────────────────────────────────────────────────
echo "[1/2] Starting backend (FastAPI on port 8000)..."
cd backend

if [ ! -d "venv" ]; then
  echo "  Creating Python virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt
python -m playwright install chromium --with-deps 2>/dev/null || python -m playwright install chromium

echo "  Backend starting at http://localhost:8000"
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

cd ..

# ── Frontend ─────────────────────────────────────────────────────────
echo "[2/2] Starting frontend (Next.js on port 3000)..."
cd src
pnpm install --silent
pnpm dev &
FRONTEND_PID=$!

cd ..

echo ""
echo "=== Both servers running ==="
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
