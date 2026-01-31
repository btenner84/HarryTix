FROM node:20-alpine

WORKDIR /app

# Copy package files and install deps
COPY package*.json ./
RUN npm install && npm install serve

# Copy source
COPY . .

# Set API URL for build (Railway injects this)
ARG VITE_API_URL=https://backend-production-2819.up.railway.app
ENV VITE_API_URL=$VITE_API_URL

# Build with env var
RUN npm run build

# Serve the dist folder
CMD ["sh", "-c", "npx serve -s dist -l ${PORT:-8080}"]
