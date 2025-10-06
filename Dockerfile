FROM node:18-slim

# Install system dependencies
# Includes Python, Java, Nginx, and envsubst utility
RUN apt-get update && apt-get install -y \
    python3 python3-pip python3-dev \
    openjdk-17-jdk \
    nginx \
    gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Install Node.js dependencies for the Java executor service
WORKDIR /app/java-executor-server
RUN npm install
WORKDIR /app

# Make start script executable
RUN chmod +x start.sh

# Expose the port that will be used by Render
EXPOSE $PORT

# Start the application
CMD ["/app/start.sh"]
