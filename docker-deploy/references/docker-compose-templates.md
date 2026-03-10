# Docker Compose Template Reference

This reference provides production-ready docker-compose.yml templates for various common patterns.

## Basic Template

```yaml
version: '3.8'

services:
  # Custom Application Service
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
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # PostgreSQL Database
  postgres:
    image: postgres:${DB_VERSION:-15.4}-alpine3.18
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8"
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

volumes:
  postgres_data:

networks:
  app-network:
    driver: bridge
```

## Multi-Service Application

```yaml
version: '3.8'

services:
  # Frontend
  frontend:
    image: ${REGISTRY_PREFIX}/myapp/frontend:${APP_VERSION:-latest}
    build:
      context: ../frontend
      dockerfile: Dockerfile
    ports:
      - "${FRONTEND_PORT:-3000}:3000"
    environment:
      - REACT_APP_API_URL=http://api:8080
    depends_on:
      - api
    networks:
      - app-network
    restart: unless-stopped

  # API Backend
  api:
    image: ${REGISTRY_PREFIX}/myapp/api:${APP_VERSION:-latest}
    build:
      context: ../api
      dockerfile: Dockerfile
    ports:
      - "${API_PORT:-8080}:8080"
    environment:
      - NODE_ENV=${ENV:-production}
      - DB_HOST=postgres
      - REDIS_HOST=redis
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Background Worker
  worker:
    image: ${REGISTRY_PREFIX}/myapp/api:${APP_VERSION:-latest}
    command: npm run worker
    environment:
      - NODE_ENV=${ENV:-production}
      - DB_HOST=postgres
      - REDIS_HOST=redis
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

  # PostgreSQL
  postgres:
    image: postgres:${DB_VERSION:-15.4}-alpine3.18
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:${REDIS_VERSION:-7.2.3}-alpine3.19
    volumes:
      - redis_data:/data
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
    image: nginx:${NGINX_VERSION:-1.25.3}-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
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

## With Monitoring Stack

```yaml
version: '3.8'

services:
  app:
    image: ${REGISTRY_PREFIX}/myapp/app:${APP_VERSION:-latest}
    build:
      context: ../app
      dockerfile: Dockerfile
    ports:
      - "${APP_PORT:-8080}:8080"
    environment:
      - METRICS_ENABLED=true
      - METRICS_PORT=9090
    networks:
      - app-network
      - monitoring
    restart: unless-stopped

  # Prometheus
  prometheus:
    image: prom/prometheus:${PROMETHEUS_VERSION:-v2.48.0}
    ports:
      - "${PROMETHEUS_PORT:-9090}:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    networks:
      - monitoring
    restart: unless-stopped

  # Grafana
  grafana:
    image: grafana/grafana:${GRAFANA_VERSION:-10.2.3}
    ports:
      - "${GRAFANA_PORT:-3000}:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./grafana/datasources:/etc/grafana/provisioning/datasources:ro
    networks:
      - monitoring
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:

networks:
  app-network:
    driver: bridge
  monitoring:
    driver: bridge
```

## With Message Queue

```yaml
version: '3.8'

services:
  api:
    image: ${REGISTRY_PREFIX}/myapp/api:${APP_VERSION:-latest}
    build:
      context: ../api
      dockerfile: Dockerfile
    environment:
      - RABBITMQ_HOST=rabbitmq
      - RABBITMQ_USER=${RABBITMQ_USER}
      - RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD}
    depends_on:
      rabbitmq:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped

  worker:
    image: ${REGISTRY_PREFIX}/myapp/worker:${APP_VERSION:-latest}
    build:
      context: ../worker
      dockerfile: Dockerfile
    environment:
      - RABBITMQ_HOST=rabbitmq
      - RABBITMQ_USER=${RABBITMQ_USER}
      - RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD}
    depends_on:
      rabbitmq:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped
    deploy:
      replicas: 3

  rabbitmq:
    image: rabbitmq:${RABBITMQ_VERSION:-3.12.6}-management-alpine
    ports:
      - "${RABBITMQ_PORT:-5672}:5672"
      - "${RABBITMQ_MGMT_PORT:-15672}:15672"
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: rabbitmq-diagnostics -q ping
      interval: 30s
      timeout: 30s
      retries: 3

volumes:
  rabbitmq_data:

networks:
  app-network:
    driver: bridge
```

## Migration Service Pattern

```yaml
version: '3.8'

services:
  # Main application
  api:
    image: ${REGISTRY_PREFIX}/myapp/api:${APP_VERSION:-latest}
    build:
      context: ../api
      dockerfile: Dockerfile
    environment:
      - DB_HOST=postgres
    depends_on:
      migration:
        condition: service_completed_successfully
    networks:
      - app-network
    restart: unless-stopped

  # Database migrations (runs once and exits)
  migration:
    image: ${REGISTRY_PREFIX}/myapp/api:${APP_VERSION:-latest}
    command: npm run migrate
    environment:
      - DB_HOST=postgres
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - app-network
    restart: "no"

  postgres:
    image: postgres:${DB_VERSION:-15.4}-alpine3.18
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:

networks:
  app-network:
    driver: bridge
```

## Best Practices

1. **Always use health checks** for services that others depend on
2. **Pin all image versions** including third-party services
3. **Use depends_on with conditions** to control startup order
4. **Set restart policies** for production resilience
5. **Separate networks** for different concerns (app vs monitoring)
6. **Use volumes** for persistent data
7. **Environment variables** for all configurable values
8. **Registry prefix** for all custom images to enable environment switching
