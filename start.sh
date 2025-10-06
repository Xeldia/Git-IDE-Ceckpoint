#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

echo "📁 Moving into /app directory..."
cd /app

echo "🔧 Running Django migrations..."
python3 manage.py migrate --noinput

echo "🎨 Collecting static files..."
python3 manage.py collectstatic --noinput

echo "🚀 Starting Gunicorn (Django backend)..."
gunicorn config.wsgi:application --bind 0.0.0.0:8000 &

echo "🧠 Starting Java executor server..."
cd /app/java-executor-server
npm start &

echo "🌐 Starting Nginx..."
nginx -g 'daemon off;'
