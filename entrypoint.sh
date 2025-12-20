#!/bin/sh

set -e

if echo "$*" | grep -q "daphne"; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput || true
fi

echo "Fixing permissions..."
chown -R appuser:appuser /app/media || true
chown -R appuser:appuser /app/staticfiles || true

chown appuser:appuser /app/celerybeat-schedule* 2>/dev/null || true

echo "Starting app as appuser..."
exec su -s /bin/sh appuser -c "$*"