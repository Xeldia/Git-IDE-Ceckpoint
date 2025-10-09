#!/bin/bash
set -e

echo "=echo "Java Web# Check WebSocket
if ! nc -z 127.0.0.1 8080; then
    echo "❌ WebSocket service check failed!"
    echo "WebSocket logs:"
    tail -n 50 /var/log/websocket.log 2>/dev/null || echo "No WebSocket logs found"
    exit 1
else
    echo "✅ WebSocket service check passed!"
fi0000): $(nc -zv 127.0.0.1 10000 2>&1)"
echo "Nginx (10000): $(nc -zv 127.0.0.1 10000 2>&1)"

# Check Djangotarting Health Check ==="

# Function to check a service
check_service() {
    local service=$1
    local url=$2
    local expected=$3
    
    echo "Checking $service..."
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    echo "$service returned status: $response (expected $expected)"
    
    if [ "$response" != "$expected" ]; then
        echo "âŒ $service check failed!"
        return 1
    else
        echo "âœ… $service check passed!"
        return 0
    fi
}

# Check if services are listening
echo "Checking ports..."
echo "Django ($DJANGO_PORT): $(nc -zv 127.0.0.1 $DJANGO_PORT 2>&1)"
echo "WebSocket ($WS_PORT): $(nc -zv 127.0.0.1 $WS_PORT 2>&1)"
echo "Nginx ($PORT): $(nc -zv 127.0.0.1 $PORT 2>&1)"

# Check Django
if ! check_service "Django" "http://127.0.0.1:8000/" "200"; then
    echo "Django service check failed"
    echo "Django logs:"
    tail -n 50 /var/log/django.log 2>/dev/null || echo "No Django logs found"
    exit 1
fi

# Check WebSocket
if ! nc -z 127.0.0.1 10000; then
    echo "âŒ WebSocket service check failed!"
    echo "WebSocket logs:"
    tail -n 50 /var/log/websocket.log 2>/dev/null || echo "No WebSocket logs found"
    exit 1
else
    echo "âœ… WebSocket service check passed!"
fi

# Check Nginx
if ! check_service "Nginx" "http://127.0.0.1:10000/" "200"; then
    echo "Nginx service check failed"
    echo "Nginx error log:"
    tail -n 50 /var/log/nginx/error.log 2>/dev/null || echo "No Nginx error log found"
    echo "Nginx access log:"
    tail -n 50 /var/log/nginx/access.log 2>/dev/null || echo "No Nginx access log found"
    exit 1
fi

echo "=== All Health Checks Passed ==="
exit 0
