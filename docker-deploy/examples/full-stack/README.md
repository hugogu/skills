# Example: Full-Stack Application Deployment

This example demonstrates a complete Docker deployment setup for a full-stack application with:
- Node.js API backend
- React frontend  
- Background worker
- PostgreSQL database
- Redis cache
- Nginx reverse proxy

## Project Structure

```
myapp/
├── deploy/
│   ├── docker-compose.yml
│   ├── docker-compose.override.yml
│   ├── .env.template
│   ├── .env
│   ├── scripts/
│   │   ├── build-and-push.sh
│   │   ├── build.sh
│   │   └── push.sh
│   ├── nginx.conf
│   └── README.md
├── services/
│   ├── api/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── src/
│   ├── frontend/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   └── src/
│   └── worker/
│       ├── Dockerfile
│       ├── package.json
│       └── src/
└── README.md
```

## Quick Start

1. **Setup environment:**
   ```bash
   cd deploy
   cp .env.template .env
   # Edit .env with your values
   ```

2. **Run locally:**
   ```bash
   docker-compose up --build
   ```

3. **Build and push for production:**
   ```bash
   ./scripts/build-and-push.sh --registry registry.example.com --version 1.0.0
   ```

4. **Deploy to production:**
   ```bash
   # On production server
   docker-compose pull
   docker-compose up -d
   ```

## Environment Configuration

### Local Development (.env)

```bash
REGISTRY_PREFIX=localhost:5000
APP_VERSION=dev
ENV=local

# Ports
API_PORT=8080
FRONTEND_PORT=3000
DB_PORT=5432
REDIS_PORT=6379

# Database
DB_VERSION=15.4
DB_NAME=myapp
DB_USER=myapp
DB_PASSWORD=devpassword

# Redis
REDIS_VERSION=7.2.3

# JWT
JWT_SECRET=dev-jwt-secret-change-in-production

# Development
DEV_HOT_RELOAD=true
DEBUG=true
```

### Production (.env)

```bash
REGISTRY_PREFIX=registry.example.com/mycompany
APP_VERSION=1.0.0
ENV=production

# Ports (only expose what needed)
API_PORT=8080
FRONTEND_PORT=80

# Database (internal ports not exposed)
DB_VERSION=15.4
DB_NAME=myapp
DB_USER=myapp
DB_PASSWORD=<generate-strong-password>

# Redis (internal only)
REDIS_VERSION=7.2.3

# JWT (generate with: openssl rand -base64 32)
JWT_SECRET=<strong-random-secret>

# Development (disabled)
DEV_HOT_RELOAD=false
DEBUG=false
```

## Files

### docker-compose.yml

```yaml
version: '3.8'

services:
  # Frontend React App
  frontend:
    image: ${REGISTRY_PREFIX}/myapp/frontend:${APP_VERSION:-latest}
    build:
      context: ../services/frontend
      dockerfile: Dockerfile
    environment:
      - REACT_APP_API_URL=/api
      - REACT_APP_ENV=${ENV:-production}
    networks:
      - app-network
    restart: unless-stopped

  # API Backend
  api:
    image: ${REGISTRY_PREFIX}/myapp/api:${APP_VERSION:-latest}
    build:
      context: ../services/api
      dockerfile: Dockerfile
    ports:
      - "${API_PORT:-8080}:8080"
    environment:
      - NODE_ENV=${ENV:-production}
      - PORT=8080
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - JWT_SECRET=${JWT_SECRET}
      - LOG_LEVEL=${LOG_LEVEL:-info}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Background Worker
  worker:
    image: ${REGISTRY_PREFIX}/myapp/worker:${APP_VERSION:-latest}
    build:
      context: ../services/worker
      dockerfile: Dockerfile
    environment:
      - NODE_ENV=${ENV:-production}
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - LOG_LEVEL=${LOG_LEVEL:-info}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped
    deploy:
      replicas: 2

  # Database Migration
  migration:
    image: ${REGISTRY_PREFIX}/myapp/api:${APP_VERSION:-latest}
    command: npm run migrate
    environment:
      - NODE_ENV=${ENV:-production}
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - app-network
    restart: "no"
    profiles:
      - migration

  # PostgreSQL Database
  postgres:
    image: postgres:${DB_VERSION:-15.4}-alpine3.18
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=C --lc-ctype=C"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d:ro
    ports:
      - "${DB_PORT:-5432}:5432"
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:${REDIS_VERSION:-7.2.3}-alpine3.19
    volumes:
      - redis_data:/data
    ports:
      - "${REDIS_PORT:-6379}:6379"
    networks:
      - app-network
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Nginx Reverse Proxy
  nginx:
    image: nginx:1.25.3-alpine
    ports:
      - "${FRONTEND_PORT:-80}:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - frontend
      - api
    networks:
      - app-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
```

### docker-compose.override.yml (Local Development)

```yaml
version: '3.8'

services:
  frontend:
    build:
      target: development
    volumes:
      - ../services/frontend:/app
      - /app/node_modules
    ports:
      - "${FRONTEND_PORT:-3000}:3000"
    environment:
      - CHOKIDAR_USEPOLLING=true
      - WATCHPACK_POLLING=true
    command: npm start

  api:
    build:
      target: development
    volumes:
      - ../services/api:/app
      - /app/node_modules
    environment:
      - DEBUG=true
      - NODE_ENV=development
    command: npm run dev

  worker:
    build:
      target: development
    volumes:
      - ../services/worker:/app
      - /app/node_modules
    environment:
      - DEBUG=true
      - NODE_ENV=development
    command: npm run dev
```

### nginx.conf

```nginx
server {
    listen 80;
    server_name localhost;

    # Frontend
    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API
    location /api/ {
        proxy_pass http://api:8080/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### Services/api/Dockerfile

```dockerfile
# Multi-stage Dockerfile for Node.js API

# Stage 1: Dependencies
FROM node:20.11.0-alpine3.19 AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Stage 2: Development
FROM node:20.11.0-alpine3.19 AS development
WORKDIR /app
RUN npm install -g nodemon
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 8080
CMD ["npm", "run", "dev"]

# Stage 3: Production
FROM node:20.11.0-alpine3.19 AS production
WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Copy dependencies
COPY --from=deps --chown=nodejs:nodejs /app/node_modules ./node_modules

# Copy application
COPY --chown=nodejs:nodejs . .

USER nodejs

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:8080/health', (r) => r.statusCode === 200 ? process.exit(0) : process.exit(1))"

CMD ["node", "server.js"]
```

### services/frontend/Dockerfile

```dockerfile
# Multi-stage Dockerfile for React Frontend

# Stage 1: Dependencies
FROM node:20.11.0-alpine3.19 AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci && npm cache clean --force

# Stage 2: Development
FROM node:20.11.0-alpine3.19 AS development
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "start"]

# Stage 3: Build
FROM node:20.11.0-alpine3.19 AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG REACT_APP_API_URL
ARG REACT_APP_ENV
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_ENV=$REACT_APP_ENV
RUN npm run build

# Stage 4: Production (Nginx)
FROM nginx:1.25.3-alpine AS production
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1
```

## Usage Commands

### Local Development

```bash
# Start all services
docker-compose up

# Start specific services
docker-compose up api postgres

# Rebuild and start
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop everything
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

### Running Migrations

```bash
# Run migrations
docker-compose --profile migration run --rm migration

# Or use the profile with up
docker-compose --profile migration up migration
```

### Production Deployment

```bash
# 1. Build and push from local machine
./scripts/build-and-push.sh --registry registry.example.com --version 1.0.0

# 2. On production server, create .env file
# 3. Pull and run
docker-compose pull
docker-compose up -d

# 4. Run migrations
docker-compose --profile migration run --rm migration
```

## Troubleshooting

### Port Already in Use

```bash
# Find what's using the port
lsof -i :5432

# Kill process or change port in .env
DB_PORT=5433
```

### Container Won't Start

```bash
# Check logs
docker-compose logs api

# Check specific container
docker-compose ps

# Inspect container
docker inspect deploy_api_1
```

### Database Connection Issues

```bash
# Check postgres is healthy
docker-compose ps

# Connect to database
docker-compose exec postgres psql -U myapp -d myapp

# Reset database (WARNING: data loss)
docker-compose down -v
docker-compose up -d postgres
```
