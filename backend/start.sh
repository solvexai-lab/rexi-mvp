#!/bin/sh
# REXI startup script — prints every step for cloud deployment debugging
set -e

PORT="${PORT:-8000}"
echo "[STARTUP] REXI API starting on port $PORT"
echo "[STARTUP] Python version: $(python --version)"
echo "[STARTUP] Uvicorn version: $(python -m uvicorn --version)"
echo "[STARTUP] Working dir: $(pwd)"
echo "[STARTUP] App path: app.main:app"
echo "[STARTUP] Launching uvicorn..."

exec python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --log-level info
