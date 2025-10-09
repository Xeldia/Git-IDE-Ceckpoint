#!/bin/bash
set -ex  # Stop script if any command fails and print each command

echo "=== Environment Info ==="
echo "Python version: $(python3 --version)"
echo "Node version: $(node --version)"
echo "Current directory: $(pwd)"
echo "Directory contents: $(ls -la)"
echo "======================="

echo "Setting up Nginx configuration..."
cp /app/nginx.conf /etc/nginx/nginx.conf
mkdir -p /run/nginx
mkdir -p /app/static  # Create static directory to avoid warning

echo "Running Django migrations..."
cd /app
echo "Current directory structure:"
ls -R /app
python3 manage.py check --deploy
python3 manage.py migrate --noinput

echo "Collecting static files..."
python3 manage.py collectstatic --noinput -v 2

echo "Starting Django application..."
export DJANGO_LOG_LEVEL=DEBUG
gunicorn config.wsgi:application --bind $HOST:$DJANGO_PORT --workers 3 --timeout 120 --access-logfile - --error-logfile - --log-level debug &

# Wait for Django to be ready
while ! nc -z localhost $DJANGO_PORT; do
  echo "Waiting for Django to be ready..."
  sleep 2
done

echo "Starting Java executor server..."
cd /app/java-executor-server
export JAVA_OPTS="-Xmx200m -XX:MaxRAMPercentage=40"
PORT=$WS_PORT HOST=$HOST node server.js &

echo "Waiting for services to be ready..."
# Wait for Django
while ! nc -z localhost 8000 2>/dev/null; do
    echo "Waiting for Django to be ready..."
    sleep 2
done

# Wait for Java WebSocket
while ! nc -z localhost 8080 2>/dev/null; do
    echo "Waiting for Java WebSocket to be ready..."
    sleep 2
done

echo "All services are ready! Starting Nginx..."
exec nginx -g "daemon off;"
