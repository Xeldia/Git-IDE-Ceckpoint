# Python & Java IDE Deployment Guide for Render

This guide provides step-by-step instructions for deploying your Python & Java IDE application to Render.

## Architecture Overview

This application consists of three main components:
1. **Django Web Application** - Serves the IDE interface and handles Python code execution
2. **Java Executor Server** - Node.js WebSocket server for Java code execution
3. **Nginx** - Reverse proxy that routes requests to the appropriate service

## Pre-Deployment Checklist

- [x] Dockerfile configured for multi-service deployment
- [x] start.sh script with proper environment variable substitution
- [x] nginx.conf with dynamic port configuration
- [x] WebSocket URL configured for both local and production environments
- [x] Health check endpoint implemented
- [x] All services properly configured to run in a single container

## Deployment Steps

### 1. Prepare Your Repository

Ensure all the following files are properly implemented and committed to your GitHub repository:

#### Dockerfile
```dockerfile
FROM node:18-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev \
    openjdk-17-jdk \
    nginx \
    gettext-base \  # For envsubst command
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Install Node.js dependencies for Java executor
WORKDIR /app/java-executor-server
RUN npm install
WORKDIR /app

# Make start script executable
RUN chmod +x start.sh

# Expose the port that will be used by Render
EXPOSE $PORT

# Start the application
CMD ["/app/start.sh"]
```

#### start.sh
```bash
#!/bin/bash
set -e  # Stop script if any command fails

# Copy nginx configuration and substitute PORT variable
envsubst '${PORT}' < /app/nginx.conf > /etc/nginx/nginx.conf

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

# Finally, start Nginx in the foreground (so container stays alive)
nginx -g "daemon off;"
```

#### nginx.conf
```nginx
worker_processes 1;

events {
    worker_connections 1024;
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    server {
        listen ${PORT:-80};
        
        # Django application
        location / {
            proxy_pass http://localhost:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Java WebSocket server
        location /ws/ {
            proxy_pass http://localhost:8080;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }
    }
}
```

#### WebSocket URL Configuration (ide/static/js/java-ide.js)
```javascript
// Get the current hostname and use it to connect to the Java server
// For Render deployment, we need to handle both local and production environments
const isProduction = window.location.hostname.includes('onrender.com');

// Since both services are running on the same domain in production,
// we just need to use the correct WebSocket protocol and port
const WS_URL = isProduction 
  ? `wss://${window.location.host}/ws/` // WebSocket endpoint on same domain with trailing slash
  : `ws://${window.location.hostname}:8080`;
```

#### Health Check Endpoint (config/urls.py)
```python
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'healthy'})

urlpatterns = [
    # ... other paths
    path('health/', health_check, name='health_check'),
    # ... other paths
]
```

### 2. Create a New Web Service on Render

1. Log in to your Render dashboard at https://dashboard.render.com/
2. Click on "New" and select "Web Service"
3. Connect your GitHub repository
4. Select the branch with your implementation

### 3. Configure the Service

- **Name**: Choose a descriptive name (e.g., python-java-ide)
- **Runtime**: Docker
- **Instance Type**:
  - Free tier will work but with limitations (sleeps after inactivity)
  - Standard ($7/month) recommended for production use
- **Environment Variables**:
  - `ALLOWED_HOSTS`: Your Render domain (e.g., your-app-name.onrender.com)
  - `DEBUG`: Set to False for production
  - `SECRET_KEY`: Generate a secure random key

### 4. Deploy Your Application

1. Click "Create Web Service"
2. Wait for the build and deployment process to complete (10-15 minutes for the initial build)
3. Once deployed, your application will be available at the provided Render URL

## Troubleshooting

### Application Crashes
- Check Render logs for startup errors
- Verify that all required environment variables are set
- Ensure the start.sh script has executable permissions

### WebSocket Connection Fails
- Verify path consistency between frontend, nginx, and Java server
- Check browser console for connection errors
- Ensure the WebSocket URL in the frontend matches the nginx configuration

### Long Build Times
- Normal for first deployment due to installing multiple runtimes (Java, Python, Node.js)
- Subsequent deployments should be faster

### "Address already in use" Errors
- Check if your start script properly backgrounds processes with &
- Ensure each service uses a different port

## Maintenance

### Updating Your Application
1. Make changes to your code
2. Commit and push to your GitHub repository
3. Render will automatically deploy the changes

### Monitoring
- Use the Render dashboard to monitor your application's health
- Check the logs for any errors or issues
- Use the health check endpoint to verify your application is running correctly

## Security Considerations

- Set `DEBUG=False` in production
- Use a strong, unique `SECRET_KEY`
- Consider adding rate limiting for code execution
- Implement proper input validation for user code

## Performance Optimization

- Consider using a larger instance type for better performance
- Implement caching for static assets
- Optimize the Java executor for faster code execution
- Use a CDN for static assets

## Conclusion

Your Python & Java IDE is now deployed on Render and accessible from anywhere. The application uses a single container to run multiple services, making it easy to deploy and maintain.