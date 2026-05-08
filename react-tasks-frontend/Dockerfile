# Stage 1: Build Vite app
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Build-time env var injection (required for Vite)
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Stage 2: Serve with nginx:alpine
FROM nginx:alpine

# Create non-root user
RUN addgroup -g 1001 -S frontendgroup && \
    adduser -u 1001 -S frontenduser -G frontendgroup

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Permissions
RUN chown -R frontenduser:frontendgroup /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html && \
    chown -R frontenduser:frontendgroup /var/cache/nginx /var/log/nginx /etc/nginx/conf.d

# Switch to non-root user
USER frontenduser

# Expose the nginx listen port used by the K3s service
EXPOSE 8080

# HEALTHCHECK as required
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]