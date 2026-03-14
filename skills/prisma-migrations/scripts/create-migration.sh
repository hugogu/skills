#!/bin/bash
# Create a new Prisma migration
# Usage: ./create-migration.sh <migration_name>

if [ -z "$1" ]; then
    echo "❌ Error: Migration name required"
    echo ""
    echo "Usage: ./create-migration.sh <migration_name>"
    echo ""
    echo "Examples:"
    echo "  ./create-migration.sh add_user_email_verified"
    echo "  ./create-migration.sh create_post_categories"
    echo "  ./create-migration.sh remove_deprecated_fields"
    exit 1
fi

MIGRATION_NAME=$1
BACKEND_DIR="${2:-./backend}"

echo "📝 Creating migration: $MIGRATION_NAME"
echo "   Backend directory: $BACKEND_DIR"
echo ""

cd "$BACKEND_DIR" || { echo "❌ Backend directory not found: $BACKEND_DIR"; exit 1; }

# Check if schema.prisma exists
if [ ! -f "prisma/schema.prisma" ]; then
    echo "❌ schema.prisma not found in $BACKEND_DIR/prisma/"
    exit 1
fi

# Create migration (create-only mode)
echo "⏳ Running: prisma migrate dev --name $MIGRATION_NAME --create-only"
npx prisma migrate dev --name "$MIGRATION_NAME" --create-only

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migration created successfully!"
    echo ""
    
    # Find the newly created migration directory
    LATEST_MIGRATION=$(ls -t prisma/migrations | grep -v migration_lock | head -1)
    echo "   Migration directory: prisma/migrations/$LATEST_MIGRATION"
    echo ""
    echo "Next steps:"
    echo "  1. Review the generated SQL: cat prisma/migrations/$LATEST_MIGRATION/migration.sql"
    echo "  2. Edit if necessary"
    echo "  3. Apply locally: docker compose restart api"
    echo "  4. Commit: git add prisma/migrations/$LATEST_MIGRATION prisma/schema.prisma"
    echo "  5. Deploy to production: ./deploy-production.sh"
else
    echo ""
    echo "❌ Migration creation failed"
    exit 1
fi
