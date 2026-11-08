FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy application source
COPY . .

# Expose backend port
EXPOSE 5000

# Start server
CMD ["node", "src/server.js"]
