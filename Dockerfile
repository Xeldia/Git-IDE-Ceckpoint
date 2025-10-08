FROM node:18-slim

# Install Python, OpenJDK, and Nginx with minimal extra packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-minimal python3-pip openjdk-17-jdk-headless nginx && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Django application
COPY . .

# Install Python dependencies
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Install Node.js dependencies for Java executor
WORKDIR /app/java-executor-server
RUN npm install --production
WORKDIR /app

# Create temp directory for Java executor
RUN mkdir -p /app/java-executor-server/temp

# Expose ports
EXPOSE 80 10000

# Set up entrypoint script
RUN echo '#!/bin/bash\n\
cp /app/nginx.conf /etc/nginx/nginx.conf\n\
mkdir -p /run/nginx\n\
# Set Java memory limits for Render free tier\n\
export JAVA_OPTS="-Xmx200m -XX:MaxRAMPercentage=40"\n\
cd /app/java-executor-server\n\
PORT=10000 node server.js &\n\
cd /app\n\
python3 manage.py migrate --noinput\n\
python3 manage.py collectstatic --noinput\n\
gunicorn config.wsgi:application --bind 0.0.0.0:8000 &\n\
nginx -g "daemon off;"\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Start services
CMD ["/app/entrypoint.sh"]