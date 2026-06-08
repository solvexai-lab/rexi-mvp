#!/bin/sh
# REXI startup script — prints every step for cloud deployment debugging
set -e

PORT="${PORT:-8000}"
echo "[STARTUP] REXI API starting on port $PORT"
echo "[STARTUP] Python version: $(python --version)"
echo "[STARTUP] Uvicorn version: $(python -m uvicorn --version)"
echo "[STARTUP] Working dir: $(pwd)"

# Verify app imports before starting uvicorn
echo "[STARTUP] Verifying imports..."
python -c "
import sys
try:
    import app.main
    print('[VERIFY] app.main: OK')
except Exception as e:
    print(f'[VERIFY] app.main: FAIL - {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo "[STARTUP] Launching uvicorn..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --log-level info
