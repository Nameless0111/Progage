#!/bin/sh
set -e

python - <<'PY'
import os
import socket
import time
from urllib.parse import urlparse

database_url = os.environ.get("DATABASE_URL", "")
if database_url:
    parsed = urlparse(database_url)
    host = parsed.hostname
    port = parsed.port or 5432

    if host:
        deadline = time.time() + 60
        while time.time() < deadline:
            try:
                with socket.create_connection((host, port), timeout=2):
                    break
            except OSError:
                time.sleep(1)
        else:
            raise SystemExit(f"Database is not reachable at {host}:{port}")
PY

python manage.py migrate --noinput

if [ "${DJANGO_COLLECTSTATIC:-0}" = "1" ]; then
    python manage.py collectstatic --noinput
fi

exec "$@"
