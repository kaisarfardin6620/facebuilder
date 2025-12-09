#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

if echo "$*" | grep -q "daphne"; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

echo "Fixing permissions for media, static, and celery schedule..."
chown -R appuser:appuser /app/media
chown -R appuser:appuser /app/staticfiles

chown -f appuser:appuser /app/celerybeat-schedule*

echo "Starting app as appuser..."
exec su -s /bin/sh appuser -c "$*"