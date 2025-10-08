#!/bin/bash
set -e  # Stop script if any command fails

# Copy nginx configuration
cp /app/nginx.conf /etc/nginx/nginx.conf

# Ensure Nginx run directory exists
mkdir -p /run/nginx

# Start Java executor server in the background
cd /app/java-executor-server
node server.js &

# Run Django migrations and collect static files
cd /app
python3 manage.py migrate --noinput
python3 manage.py collectstatic --noinput

# Start Gunicorn in the background
gunicorn config.wsgi:application --bind 0.0.0.0:8000 &

# Wait for Gunicorn to initialize (5 seconds)
echo "Waiting for Gunicorn to initialize..."
sleep 5

# Finally, start Nginx in the foreground (so container stays alive)
nginx -g "daemon off;"
