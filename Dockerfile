FROM node:18-slim

# Install required packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    netcat-openbsd \
    nginx \
    openjdk-17-jdk-headless \
    python3-minimal \
    python3-pip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV DEBUG=True

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

# Expose port (Render requires port 10000)
EXPOSE 10000

# Copy startup scripts
COPY start.sh /app/start.sh
COPY healthcheck.sh /app/healthcheck.sh

# Make scripts executable
RUN chmod +x /app/start.sh /app/healthcheck.sh

# Start services
CMD ["/app/start.sh"]