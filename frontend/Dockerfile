FROM node:20-alpine

WORKDIR /app

# Copy package files and install deps
COPY package*.json ./
RUN npm ci && npm install serve

# Copy source and build
COPY . .
RUN npm run build

# Serve the dist folder
CMD ["sh", "-c", "npx serve -s dist -l ${PORT:-8080}"]
