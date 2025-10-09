FROM node:18-slim

# Install required packages and set up the environment
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    netcat-openbsd \
    nginx \
    openjdk-17-jdk-headless \
    python3-minimal \
    python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory and environment variables
WORKDIR /app
ENV PORT=10000 \
    WS_PORT=8080 \
    DJANGO_PORT=8000 \
    HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install Python dependencies first (for better caching)
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy Django application (after dependencies for better caching)
COPY . .
RUN rm -f .env

# Install Node.js dependencies for Java executor
WORKDIR /app/java-executor-server
RUN npm install --production
WORKDIR /app

# Create temp directory for Java executor
RUN mkdir -p /app/java-executor-server/temp

# Expose the port that will be used
EXPOSE $PORT

# Environment variables for render
ENV PORT=10000
ENV WS_PORT=8080
ENV DJANGO_PORT=8000
ENV HOST=0.0.0.0

# Copy startup scripts
COPY start.sh /app/start.sh
COPY healthcheck.sh /app/healthcheck.sh

# Make scripts executable
RUN chmod +x /app/start.sh /app/healthcheck.sh

# Start services
CMD ["/app/start.sh"]