FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Expose port
EXPOSE 8080

# Start preview server
CMD ["sh", "-c", "npm run preview -- --host --port ${PORT:-8080}"]
