#!/bin/sh

set -e

if echo "$*" | grep -q "daphne"; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

echo "Fixing permissions for /app/media and /app/staticfiles..."
chown -R appuser:appuser /app/media
chown -R appuser:appuser /app/staticfiles

echo "Starting app as appuser..."
exec su -s /bin/sh appuser -c "$*"