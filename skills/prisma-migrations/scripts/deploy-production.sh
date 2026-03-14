#!/bin/bash
# Production deployment script with database backup
# Usage: ./deploy-production.sh [environment]

ENV=${1:-production}
COMPOSE_FILE="docker-compose.prod.yml"
DB_CONTAINER="doc-compare-postgres-1"
API_CONTAINER="doc-compare-api-1"
BACKUP_DIR="./backups"

echo "🚀 Starting production deployment..."
echo "   Environment: $ENV"
echo "   Compose file: $COMPOSE_FILE"
echo ""

# 1. Backup database first
echo "💾 Creating database backup..."
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"

if docker ps | grep -q "$DB_CONTAINER"; then
    docker exec "$DB_CONTAINER" pg_dump -U dict dictdb > "$BACKUP_FILE"
    echo "   ✅ Backup saved to: $BACKUP_FILE"
else
    echo "   ⚠️  Database container not running, skipping backup"
fi

echo ""

# 2. Pull latest code
echo "📥 Pulling latest code..."
git pull origin main || { echo "❌ Failed to pull code"; exit 1; }
echo "   ✅ Code updated"

echo ""

# 3. Build new images
echo "🏗️  Building new images..."
docker compose -f "$COMPOSE_FILE" build || { echo "❌ Build failed"; exit 1; }
echo "   ✅ Build complete"

echo ""

# 4. Apply migrations
echo "🔄 Applying database migrations..."
docker compose -f "$COMPOSE_FILE" run --rm api \
    sh -c "npx prisma migrate deploy" || { echo "❌ Migration failed"; exit 1; }
echo "   ✅ Migrations applied"

echo ""

# 5. Start services
echo "▶️  Starting services..."
docker compose -f "$COMPOSE_FILE" up -d || { echo "❌ Failed to start services"; exit 1; }
echo "   ✅ Services started"

echo ""

# 6. Verify
echo "🔍 Verifying deployment..."
sleep 5

# Check migration status
if docker ps | grep -q "$API_CONTAINER"; then
    docker exec "$API_CONTAINER" npx prisma migrate status
    echo ""
    
    # Health check
    echo "🏥 Health check:"
    if curl -sf http://localhost:3000/api/v1/health > /dev/null 2>&1; then
        echo "   ✅ API is healthy"
    else
        echo "   ⚠️  API health check failed (may need more time to start)"
    fi
else
    echo "   ⚠️  API container not found"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Useful commands:"
echo "  - View logs: docker compose -f $COMPOSE_FILE logs -f api"
echo "  - Check status: docker compose -f $COMPOSE_FILE ps"
echo "  - Rollback: docker exec $DB_CONTAINER psql -U dict -d dictdb -f $BACKUP_FILE"
