#!/bin/bash
set -e

export DJANGO_SETTINGS_MODULE=config.settings.prod

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Compiling translations..."
python manage.py compilemessages --ignore=.venv 2>/dev/null || true

echo "Starting Gunicorn..."
gunicorn config.wsgi --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120
