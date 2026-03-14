---
name: prisma-migrations
description: Use when making database schema changes in Node.js + Prisma projects to ensure consistency and traceability across all environments
---

# Prisma Migrations Best Practices

## Overview

Direct SQL changes create invisible drift between environments. Migration files provide:
- **Traceability**: Complete history of schema changes
- **Consistency**: Same schema in dev, staging, and production
- **Reversibility**: Ability to roll back changes
- **Collaboration**: Team members can see and review schema changes

**Core Principle**: ALL database schema changes MUST go through Prisma Migrate.

## The Golden Rule

```
NO DIRECT SQL FOR SCHEMA CHANGES
```

Exceptions (rare):
- Performance optimizations (indexes) that don't affect application logic
- Emergency hotfixes (must be followed by proper migration)

## When to Use This Skill

Use this workflow when:
- Adding/modifying fields in Prisma schema
- Creating new models/tables
- Modifying relationships
- Any `prisma/schema.prisma` change

## Required Setup

### 1. Dockerfile Configuration

Development and production stages MUST include OpenSSL:

```dockerfile
FROM base AS development
RUN apk add --no-cache openssl3 ca-certificates  # REQUIRED for Prisma Migrate
RUN npm install
RUN npx prisma generate
COPY . .
EXPOSE 3000
# Auto-run migrations on container start
CMD ["sh", "-c", "npx prisma migrate deploy && npm run dev"]

FROM base AS production
RUN apk add --no-cache openssl3 ca-certificates  # REQUIRED
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/prisma ./prisma
COPY package*.json ./
RUN mkdir -p /data/uploads
EXPOSE 3000
CMD ["sh", "-c", "npx prisma migrate deploy && node dist/server.js"]
```

### 2. Docker Compose Configuration

For development (`docker-compose.override.yml`):
```yaml
api:
  build:
    target: development
  volumes:
    - ./backend/src:/app/src
    - ./backend/prisma:/app/prisma
  command: ["sh", "-c", "npx prisma generate && npx prisma migrate deploy && npm run dev"]
```

For production (`docker-compose.prod.yml`):
```yaml
api:
  command: ["sh", "-c", "npx prisma migrate deploy && node dist/server.js"]
```

## The Migration Workflow

### Phase 1: Create Migration

```bash
# From host machine (NOT inside container)
cd backend
npx prisma migrate dev --name <descriptive_name> --create-only
```

**Naming conventions:**
- `add_user_email_verified` - Add column
- `create_post_categories` - Create table
- `rename_user_name_to_username` - Rename field
- `remove_deprecated_fields` - Remove fields
- `add_entry_sequence` - Add feature-specific field

### Phase 2: Review Migration

1. Check generated file in `prisma/migrations/<timestamp>_<name>/migration.sql`
2. Ensure SQL is correct and safe
3. For complex changes, add comments

### Phase 3: Apply Migration Locally

```bash
# Container will auto-apply on restart
docker compose restart api

# Or manually
docker exec <container> npx prisma migrate deploy
```

### Phase 4: Baseline Production (if needed)

If production database predates migrations:

```bash
# Mark existing schema as baseline
docker exec <container> npx prisma migrate resolve --applied <migration_name>
```

## Handling Common Scenarios

### Scenario 1: New Project Setup

```bash
# 1. Initialize migrations
npx prisma migrate dev --name init

# 2. Commit migration files
git add prisma/migrations/
git commit -m "chore: initialize database migrations"

# 3. Production baseline (one-time)
docker exec <prod_container> npx prisma migrate resolve --applied <timestamp>_init
```

### Scenario 2: Adding a New Field

```bash
# 1. Edit schema.prisma
model Entry {
  // ... existing fields
  entrySequence Int?  // Add new field
}

# 2. Create migration
npx prisma migrate dev --name add_entry_sequence --create-only

# 3. Review generated SQL
# File: prisma/migrations/<timestamp>_add_entry_sequence/migration.sql

# 4. Apply
docker compose restart api

# 5. Commit
git add prisma/migrations/ prisma/schema.prisma
git commit -m "feat: add entry sequence field"
```

### Scenario 3: Container Has No OpenSSL

**Error:**
```
Prisma schema engine: SyntaxError: Unexpected token 'E', "Error load"... is not valid JSON
```

**Solution:**
```dockerfile
# Add to Dockerfile (both dev and prod stages)
RUN apk add --no-cache openssl3 ca-certificates
```

Then rebuild:
```bash
docker compose build api
docker compose up -d api
```

### Scenario 4: Migration Exists But Database Is Empty

```bash
# Mark all existing migrations as applied
docker exec <container> npx prisma migrate resolve --applied <migration_1>
docker exec <container> npx prisma migrate resolve --applied <migration_2>
# ... etc

# Or mark all at once (nuclear option)
docker exec <container> sh -c "for m in $(ls prisma/migrations | grep -v migration_lock); do npx prisma migrate resolve --applied $m; done"
```

### Scenario 5: Production Deployment

```bash
# 1. Backup database first
docker exec doc-compare-postgres-1 pg_dump -U dict dictdb > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Apply migrations
docker compose -f docker-compose.prod.yml run --rm api \
  sh -c "npx prisma migrate deploy"

# 3. Verify
docker exec <prod_container> npx prisma migrate status
```

## Deployment Checklist

Before deploying schema changes to production:

- [ ] Migration file created and committed
- [ ] Migration tested locally
- [ ] Database backed up (production)
- [ ] Dockerfile includes OpenSSL
- [ ] Docker Compose includes migrate command
- [ ] Migration status verified: `prisma migrate status`
- [ ] Schema verified: `\d table_name` in psql
- [ ] Application starts successfully
- [ ] Smoke tests pass

## Anti-Patterns (NEVER DO)

❌ **Direct SQL without migration:**
```bash
docker exec postgres psql -c "ALTER TABLE entries ADD COLUMN foo TEXT;"
```

❌ **Manual schema changes in production:**
```bash
psql -c "DROP COLUMN users.old_field;"
```

❌ **Skipping migration creation:**
```bash
# Just editing schema.prisma without migrate dev
```

❌ **Different schemas per environment:**
```bash
# Dev has column, prod doesn't
```

## Verification Commands

```bash
# Check migration status
docker exec <container> npx prisma migrate status

# View pending migrations
docker exec <container> npx prisma migrate status | grep "not yet applied"

# Generate diff from current DB to schema
docker exec <container> npx prisma migrate diff --from-schema-datasource prisma/schema.prisma --to-schema-datamodel prisma/schema.prisma --script

# Validate schema without applying
docker exec <container> npx prisma validate
```

## Project Structure

```
project/
├── backend/
│   ├── prisma/
│   │   ├── schema.prisma       # Source of truth
│   │   ├── migrations/         # Migration history
│   │   │   ├── migration_lock.toml
│   │   │   ├── 20240101000000_init/
│   │   │   │   └── migration.sql
│   │   │   └── 20240313140000_add_entry_sequence/
│   │   │       └── migration.sql
│   │   └── migrations/
│   └── Dockerfile              # Must have OpenSSL
├── docker-compose.yml
└── docker-compose.prod.yml
```

## Troubleshooting

### "Can't reach database server"
- Check container can reach postgres:5432
- Verify DATABASE_URL environment variable

### "SyntaxError: Unexpected token"
- Missing OpenSSL in container
- Fix: Add `RUN apk add --no-cache openssl3` to Dockerfile

### "Migration already applied"
- Use `prisma migrate resolve --applied <name>` to mark as baseline

### "Database schema is not empty"
- Existing database needs baseline migration
- Run `prisma migrate resolve --applied <init_migration>`

## Best Practices Summary

1. **Always use migrations** - Never direct SQL for schema changes
2. **Commit migrations** - They are part of your codebase
3. **Review generated SQL** - Before applying
4. **Test locally first** - Verify migration works
5. **Backup before production** - Always have a rollback plan
6. **Use descriptive names** - Clear migration names help debugging
7. **One logical change per migration** - Don't bundle unrelated changes
8. **Keep migrations backward compatible** - When possible (zero-downtime deployments)

## References

- [Prisma Migrate Documentation](https://www.prisma.io/docs/concepts/components/prisma-migrate)
- [Production Deployment Guide](https://www.prisma.io/docs/guides/deployment/deploy-database-changes-with-prisma-migrate)
- [Troubleshooting Migrations](https://www.prisma.io/docs/guides/migrate/troubleshooting)
