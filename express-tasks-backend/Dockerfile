# Stage 1: Builder
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies (cache optimization)
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Stage 2: Production (lightweight image)
FROM node:20-alpine

WORKDIR /app

# Copy only necessary artifacts from builder
COPY --from=builder /app /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S backenduser -u 1001

# Change ownership
RUN chown -R backenduser:nodejs /app
USER backenduser

# Default port (can be overridden in Compose)
ENV PORT=3000

# Expose port
EXPOSE 3000

# HEALTHCHECK as required (HTTP on /health)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:${PORT}/health || exit 1

# Start command
CMD ["node", "server.js"]