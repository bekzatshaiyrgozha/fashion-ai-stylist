#!/bin/sh
set -e

if [ -n "$POSTGRES_HOST" ]; then
  echo "Waiting for database at $POSTGRES_HOST:$POSTGRES_PORT..."
  python - <<PY
import os, time, socket
host = os.environ.get('POSTGRES_HOST')
port = int(os.environ.get('POSTGRES_PORT', '5432'))
while True:
    try:
        s = socket.create_connection((host, port), timeout=1)
        s.close()
        break
    except Exception:
        time.sleep(0.5)
print('Database available')
PY
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
