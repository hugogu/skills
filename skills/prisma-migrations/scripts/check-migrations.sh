#!/bin/bash
# Check Prisma migration status in Docker container
# Usage: ./check-migrations.sh [container_name]

CONTAINER=${1:-doc-compare-api-1}

echo "🔍 Checking Prisma migration status in container: $CONTAINER"
echo ""

# Check if container is running
if ! docker ps | grep -q "$CONTAINER"; then
    echo "❌ Container $CONTAINER is not running"
    echo "   Start it first: docker compose up -d api"
    exit 1
fi

# Check migration status
echo "📋 Migration Status:"
docker exec "$CONTAINER" npx prisma migrate status

echo ""
echo "✅ Check complete!"
