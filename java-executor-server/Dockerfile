FROM node:18-slim

# Install OpenJDK
RUN apt-get update && apt-get install -y openjdk-17-jdk && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy server files
COPY . .

# Create temp directory
RUN mkdir -p temp

# Expose port
EXPOSE 8080

# Start server
CMD ["node", "server.js"]