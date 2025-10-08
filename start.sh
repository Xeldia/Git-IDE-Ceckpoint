#!/bin/bash
set -e  # Stop script if any command fails

echo "Setting up Nginx configuration..."
cp /app/nginx.conf /etc/nginx/nginx.conf
mkdir -p /run/nginx

echo "Starting Java executor server..."
cd /app/java-executor-server
export JAVA_OPTS="-Xmx200m -XX:MaxRAMPercentage=40"
PORT=10000 node server.js &
cd /app

echo "Running Django migrations..."
python3 manage.py migrate --noinput

echo "Collecting static files..."
python3 manage.py collectstatic --noinput

echo "Starting Django application..."
gunicorn config.wsgi:application --bind 0.0.0.0:8000 &

echo "Waiting for services to be ready..."
# Wait for Django
while ! nc -z localhost 8000 2>/dev/null; do
    echo "Waiting for Django to be ready..."
    sleep 2
done

# Wait for Java WebSocket
while ! nc -z localhost 10000 2>/dev/null; do
    echo "Waiting for Java WebSocket to be ready..."
    sleep 2
done

echo "All services are ready! Starting Nginx..."
exec nginx -g "daemon off;"
