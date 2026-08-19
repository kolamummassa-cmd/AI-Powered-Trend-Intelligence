#!/usr/bin/env bash
# Container entrypoint. Runs one-off setup (migrate/seed/collectstatic),
# then hands off to honcho, which supervises nginx + gunicorn + Next.js +
# Celery worker + Celery beat together (see Procfile).
set -euo pipefail

echo "=== Running migrations ==="
cd /app/backend
python manage.py migrate --noinput

echo "=== Seeding RSS platforms (idempotent) ==="
python manage.py seed_platforms

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Configuring nginx for port ${PORT:-8080} ==="
export PORT="${PORT:-8080}"
envsubst '${PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

echo "=== Starting all processes (nginx, gunicorn, next, celery worker, celery beat) ==="
cd /app
exec honcho start -f Procfile
