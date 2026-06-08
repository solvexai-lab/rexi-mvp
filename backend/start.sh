#!/bin/sh
# REXI startup script — prints every step for cloud deployment debugging
set -e

PORT="${PORT:-8000}"
echo "[STARTUP] REXI API starting on port $PORT"
echo "[STARTUP] Python version: $(python --version)"
echo "[STARTUP] Uvicorn version: $(python -m uvicorn --version)"
echo "[STARTUP] Working dir: $(pwd)"
echo "[STARTUP] PYTHONPATH: $PYTHONPATH"

# Verify critical imports before starting uvicorn
echo "[STARTUP] Verifying imports..."
python -c "
import sys
print('[VERIFY] sys.path:', sys.path[:5])
try:
    import contractguard.prompts
    print('[VERIFY] contractguard.prompts: OK')
except Exception as e:
    print(f'[VERIFY] contractguard.prompts: FAIL - {e}')
    sys.exit(1)
try:
    import legal_redline.diff
    print('[VERIFY] legal_redline.diff: OK')
except Exception as e:
    print(f'[VERIFY] legal_redline.diff: FAIL - {e}')
    sys.exit(1)
try:
    import app.main
    print('[VERIFY] app.main: OK')
except Exception as e:
    print(f'[VERIFY] app.main: FAIL - {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
print('[VERIFY] All imports OK')
"

echo "[STARTUP] Launching uvicorn..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --log-level info
