FROM node:18-slim

# Install OpenJDK for Java compilation and execution
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    openjdk-17-jdk-headless && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy source code
COPY . .

# Create temp directory for Java files
RUN mkdir -p temp

# Environment variables
ENV PORT=8080 \
    HOST=0.0.0.0 \
    MAX_EXECUTION_TIME=30000

# Expose port
EXPOSE $PORT

# Start the server
CMD ["node", "server.js"]