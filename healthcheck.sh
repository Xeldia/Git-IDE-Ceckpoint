#!/bin/bash

# Function to check if a port is accepting connections
check_port() {
    local port=$1
    timeout 1 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/$port"
    return $?
}

# Wait for Django to be ready
while ! check_port 8000; do
    echo "Waiting for Django to be ready..."
    sleep 2
done

# Wait for Java WebSocket to be ready
while ! check_port 10000; do
    echo "Waiting for Java WebSocket to be ready..."
    sleep 2
done

echo "All services are ready!"