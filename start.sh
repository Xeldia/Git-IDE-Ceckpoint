#!/bin/bash
set -e

echo "Collecting static files..."
python3 manage.py collectstatic --noinput

echo "Applying database migrations..."
python3 manage.py migrate --noinput

echo "Starting Gunicorn..."
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT &

# Wait a few seconds to make sure Gunicorn is ready
sleep 5

echo "Starting Nginx..."
nginx -g "daemon off;"
