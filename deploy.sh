#!/bin/bash
set -e

export DJANGO_SETTINGS_MODULE=config.settings.prod

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Compiling translations..."
python manage.py compilemessages --ignore=.venv 2>/dev/null || true

echo "Starting Gunicorn..."
gunicorn -b 0.0.0.0:8000 config.wsgi:application  --access-logfile '-' --error-logfile '-' --log-level debug --timeout 600
