---
name: docker-deploy
description: Set up complete Docker-based virtualized deployment infrastructure with docker-compose, multi-environment support (local build vs production images), registry management with prefix switching, fine-grained versioning, and network-aware build/push scripts. Use this skill when users ask for Docker deployment setup, containerization, docker-compose configuration, multi-environment deployments, registry management, or building production-ready container infrastructure. Essential for projects requiring local development with Docker and production deployment to private registries.
---

# Docker Deployment Infrastructure Setup

This skill creates a complete, production-ready Docker deployment infrastructure with support for multiple environments, registry management, and network-aware operations.

## Core Principles

1. **Single Command Deployment**: One `docker-compose.yml` brings up the entire stack including all dependencies
2. **Environment Separation**: Local builds from Dockerfiles; production uses prebuilt images
3. **Registry Flexibility**: Prefix-based registry switching for easy local/prod transitions
4. **Version Pinning**: All third-party images use specific versions (no `latest` tags)
5. **Network Awareness**: Image pushes happen at the end after all local operations succeed

## What Gets Created

```
deploy/
├── docker-compose.yml          # Main orchestration file
├── docker-compose.override.yml # Local development overrides (optional)
├── .env.template              # Environment variable template
├── .env                       # Local environment config (gitignored)
├── scripts/
│   ├── build.sh              # Build images locally
│   ├── push.sh               # Push to registry
│   └── build-and-push.sh     # Complete build + push workflow
├── services/
│   ├── service-a/
│   │   └── Dockerfile
│   └── service-b/
│       └── Dockerfile
└── README.md                  # Usage instructions
```

## Workflow

### Step 1: Analyze Project Structure

First, understand the project:
- Identify all services that need containers
- Identify third-party dependencies (databases, caches, message queues)
- Determine port mappings and environment variables
- Check for existing Docker configurations

### Step 2: Create Environment Configuration

Create `.env.template` with all configurable values:

```bash
# Registry Configuration
REGISTRY_PREFIX=localhost:5000  # Change for production: registry.example.com

# Application Versions
APP_VERSION=1.0.0

# Service Configuration
SERVICE_A_PORT=8080
SERVICE_B_PORT=8081

# Database Configuration  
DB_VERSION=15.4
DB_NAME=myapp
DB_USER=myuser
DB_PASSWORD=changeme
DB_PORT=5432

# Cache Configuration
REDIS_VERSION=7.2.3
REDIS_PORT=6379

# Environment
ENV=local  # local, staging, production
```

Key rules:
- **Always pin versions**: Use `15.4` not `latest` or `15`
- **Make ports configurable**: Don't hardcode in docker-compose
- **Separate secrets**: Database passwords, API keys in .env (not in template)
- **Document every variable**: Add comments explaining usage

### Step 3: Create Dockerfiles

For each application service, create optimized Dockerfiles:

**Multi-stage build example:**
```dockerfile
# Stage 1: Build
FROM node:20.11.0-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Stage 2: Production
FROM node:20.11.0-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package.json ./
EXPOSE 3000
USER node
CMD ["node", "dist/main.js"]
```

Requirements:
- Use **specific versions only** (e.g., `node:20.11.0-alpine`, not `node:alpine`)
- Use multi-stage builds to minimize image size
- Run as non-root user when possible
- Include only necessary files (use .dockerignore)

### Step 4: Create Docker Compose Configuration

Create the main `docker-compose.yml` using registry prefix pattern:

```yaml
version: '3.8'

services:
  # Application Services
  api:
    image: ${REGISTRY_PREFIX}/myapp/api:${APP_VERSION:-latest}
    build:
      context: ../services/api
      dockerfile: Dockerfile
    ports:
      - "${API_PORT:-8080}:8080"
    environment:
      - NODE_ENV=${ENV:-production}
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Third-party Services (Always pinned versions)
  postgres:
    image: postgres:15.4-alpine3.18
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
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

  redis:
    image: redis:7.2.3-alpine3.19
    volumes:
      - redis_data:/data
    ports:
      - "${REDIS_PORT:-6379}:6379"
    networks:
      - app-network
    restart: unless-stopped
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
```

**Critical patterns:**
- Use `${REGISTRY_PREFIX}` for all custom images
- Use specific versions for third-party images (postgres:15.4-alpine3.18, not postgres:latest)
- Include `build` context for local development
- Set `restart: unless-stopped` for production resilience
- Add healthchecks for dependencies
- Use depends_on with conditions for startup ordering

### Step 5: Create Build and Push Scripts

Create `scripts/build-and-push.sh` with network-aware workflow:

```bash
#!/bin/bash
set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Load environment
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    source "${PROJECT_ROOT}/.env"
    set +a
fi

# Configuration
REGISTRY_PREFIX="${REGISTRY_PREFIX:-localhost:5000}"
APP_VERSION="${APP_VERSION:-latest}"
SERVICES=("api" "worker" "frontend")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Track images to push
IMAGES_TO_PUSH=()

# Step 1: Run tests and checks (offline operations)
log_info "Step 1: Running pre-build checks..."

# Add linting, testing, security scans here
# These should work without network access to registry

# Step 2: Build images locally (may need internet for base images)
log_info "Step 2: Building images..."
cd "${PROJECT_ROOT}"

for service in "${SERVICES[@]}"; do
    log_info "Building ${service}..."
    docker-compose build "${service}"
    IMAGES_TO_PUSH+=("${REGISTRY_PREFIX}/myapp/${service}:${APP_VERSION}")
done

# Step 3: Run integration tests (offline)
log_info "Step 3: Running integration tests..."
docker-compose up -d postgres redis
sleep 5  # Wait for dependencies

# Run tests here
# docker-compose run --rm api npm test

# Cleanup test containers
docker-compose down

# Step 4: Tag images with registry prefix
log_info "Step 4: Tagging images..."
for service in "${SERVICES[@]}"; do
    local_image="myapp_${service}"
    target_image="${REGISTRY_PREFIX}/myapp/${service}:${APP_VERSION}"
    
    log_info "Tagging ${local_image} -> ${target_image}"
    docker tag "${local_image}:latest" "${target_image}"
done

# Step 5: Push all images (network operation - last!)
log_info "Step 5: Pushing images to registry..."
log_warn "Switching to registry network if needed..."

for image in "${IMAGES_TO_PUSH[@]}"; do
    log_info "Pushing ${image}..."
    docker push "${image}"
done

log_info "Build and push completed successfully!"
log_info "Images pushed to: ${REGISTRY_PREFIX}"
```

Also create standalone scripts:

**scripts/build.sh:**
```bash
#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."
docker-compose build
```

**scripts/push.sh:**
```bash
#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    source "${PROJECT_ROOT}/.env"
    set +a
fi

REGISTRY_PREFIX="${REGISTRY_PREFIX:-localhost:5000}"
APP_VERSION="${APP_VERSION:-latest}"
SERVICES=("api" "worker" "frontend")

for service in "${SERVICES[@]}"; do
    image="${REGISTRY_PREFIX}/myapp/${service}:${APP_VERSION}"
    echo "Pushing ${image}..."
    docker push "${image}"
done
```

### Step 6: Environment-Specific Overrides

Create `docker-compose.override.yml` for local development:

```yaml
version: '3.8'

services:
  api:
    build:
      context: ../services/api
      dockerfile: Dockerfile
      target: development  # Use dev stage if multi-stage
    volumes:
      - ../services/api:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - DEBUG=true
    command: npm run dev  # Hot reload

  postgres:
    ports:
      - "5432:5432"  # Always expose locally
```

This file is automatically used by docker-compose for local development but ignored in production.

## Environment Switching

### Local Development

```bash
cd deploy
# Copy template
cp .env.template .env
# Edit .env with local values
# REGISTRY_PREFIX=localhost:5000

# Build and run locally
docker-compose up --build
```

### Production Deployment

```bash
# On production server, use prebuilt images
cd deploy
cp .env.template .env
# Edit .env:
# REGISTRY_PREFIX=registry.example.com
# APP_VERSION=1.2.3

# Pull and run (no build needed)
docker-compose pull
docker-compose up -d
```

### Staging/Testing Prebuilt Images Locally

```bash
# Test production images locally
cd deploy
REGISTRY_PREFIX=registry.example.com APP_VERSION=1.2.3 docker-compose pull
REGISTRY_PREFIX=registry.example.com APP_VERSION=1.2.3 docker-compose up
```

## Registry Management

### Supported Registry Formats

The `REGISTRY_PREFIX` supports various formats:

- **Local registry**: `localhost:5000`
- **Docker Hub**: `docker.io/username` or just `username`
- **GitHub Container Registry**: `ghcr.io/username`
- **AWS ECR**: `123456789012.dkr.ecr.us-east-1.amazonaws.com`
- **GCP GCR**: `gcr.io/project-id`
- **Azure ACR**: `myregistry.azurecr.io`

### Multi-Registry Example

```bash
# .env file for different environments
# Development:
REGISTRY_PREFIX=localhost:5000

# Staging:
REGISTRY_PREFIX=registry-staging.example.com

# Production:
REGISTRY_PREFIX=registry-prod.example.com
```

## Security Best Practices

1. **Never commit .env files**: Add to .gitignore
2. **Use non-root users** in Dockerfiles
3. **Scan images** before pushing (add to build script):
   ```bash
   docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
     aquasec/trivy image ${image}
   ```
4. **Pin base image digests** for maximum security:
   ```dockerfile
   FROM node:20.11.0-alpine@sha256:abcd1234...
   ```
5. **Use secrets management** for sensitive env vars in production

## Common Patterns

### Adding a New Service

1. Create Dockerfile in `services/new-service/`
2. Add service to `docker-compose.yml`:
   ```yaml
   new-service:
     image: ${REGISTRY_PREFIX}/myapp/new-service:${APP_VERSION}
     build:
       context: ../services/new-service
       dockerfile: Dockerfile
   ```
3. Add to `SERVICES` array in build scripts
4. Add configuration to `.env.template`

### Database Migrations

```yaml
services:
  migration:
    image: ${REGISTRY_PREFIX}/myapp/api:${APP_VERSION}
    command: npm run migrate
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      - DB_HOST=postgres
      - DB_URL=postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
```

Run: `docker-compose run --rm migration`

### Health Checks

Always include health checks for services that others depend on:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## Troubleshooting

### Port Conflicts
If ports are already in use, override in `.env`:
```bash
API_PORT=8081
DB_PORT=5433
```

### Registry Authentication
Login to registry before push:
```bash
docker login registry.example.com
# Or for AWS ECR:
aws ecr get-login-password | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
```

### Image Not Found
Ensure `REGISTRY_PREFIX` and `APP_VERSION` match between build and run:
```bash
# Check available tags
docker images | grep myapp

# Verify env vars
cat .env | grep -E '(REGISTRY_PREFIX|APP_VERSION)'
```

## Implementation Checklist

When setting up Docker deployment for a project, ensure:

- [ ] All third-party images use pinned versions (not `latest`)
- [ ] `.env.template` created with all variables documented
- [ ] `.env` added to `.gitignore`
- [ ] `docker-compose.yml` uses `${REGISTRY_PREFIX}` for custom images
- [ ] Build scripts push images at the end (after local operations)
- [ ] Health checks defined for interdependent services
- [ ] Multi-stage Dockerfiles for optimized images
- [ ] Services run as non-root users
- [ ] Volume persistence configured for databases
- [ ] README with usage instructions created
- [ ] Scripts are executable (`chmod +x scripts/*.sh`)

## Example Usage

After setup, typical workflow:

```bash
# Local development
cd deploy
docker-compose up --build

# Build and push for production
./scripts/build-and-push.sh

# Deploy to production server
ssh production-server
cd /opt/myapp/deploy
docker-compose pull
docker-compose up -d
```
