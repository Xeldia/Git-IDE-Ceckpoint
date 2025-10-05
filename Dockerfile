FROM node:18-slim

# Install Python, OpenJDK, and Nginx
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-dev openjdk-17-jdk nginx && \
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
EXPOSE 8000 8080

# Copy startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Start both services
CMD ["/app/start.sh"]