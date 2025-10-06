#!/usr/bin/env bash
set -o errexit  # Exit on error
set -o pipefail # Catch pipeline errors
set -o nounset  # Treat unset vars as errors

echo "📦 Starting deployment setup..."

# -------------------------------
# 1️⃣ Move into app directory
# -------------------------------
cd /app
echo "📁 Current directory: $(pwd)"

# -------------------------------
# 2️⃣ Run Django setup
# -------------------------------
echo "🔧 Running Django migrations..."
python3 manage.py migrate --noinput

echo "🎨 Collecting static files..."
python3 manage.py collectstatic --noinput

# -------------------------------
# 3️⃣ Start Django backend (Gunicorn)
# -------------------------------
echo "🚀 Starting Gunicorn (Django backend)..."
gunicorn config.wsgi:application --bind 0.0.0.0:8000 &
DJANGO_PID=$!

# -------------------------------
# 4️⃣ Start Java executor server (Node.js)
# -------------------------------
echo "🧠 Starting Java executor server..."
cd /app/java-executor-server
npm start &
NODE_PID=$!

# -------------------------------
# 5️⃣ Return to /app and start Nginx
# -------------------------------
cd /app
echo "🌐 Starting Nginx reverse proxy..."
nginx -g 'daemon off;'

# -------------------------------
# 6️⃣ Cleanup on exit (optional but safe)
# -------------------------------
trap "echo '🛑 Shutting down...'; kill $DJANGO_PID $NODE_PID" EXIT
