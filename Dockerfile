FROM node:18-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev \
    openjdk-17-jdk \
    nginx \
    gettext-base && \
    rm -rf /var/lib/apt/lists/*

# Set working directoryss
WORKDIR /app

# Copy all project files
COPY . .

# Install Python dependencies
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Install Node.js dependencies for Java executor
WORKDIR /app/java-executor-server
RUN npm install
WORKDIR /app

# Make sure start.sh is executable
RUN chmod +x /app/start.sh

# Environment setup (Render provides PORT automatically)
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV PORT=80

# Expose the Nginx port
EXPOSE 80

# Start everything through start.sh
CMD ["bash", "/app/start.sh"]
