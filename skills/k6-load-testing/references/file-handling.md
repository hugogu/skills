# File Handling Strategy

This document explains how the k6-load-testing skill handles existing files and provides guidance on safe integration.

## The Problem

The original skill implementation used:
```bash
cp -r <skill-path>/assets/templates/* ./
```

This approach **overwrites** existing project files:
- `docker-compose.yml` - Project's service definitions
- `README.md` - Project documentation
- `Makefile` - Project build commands

## The Solution

The skill now provides **three integration strategies** to safely add k6 load testing to any project.

## Integration Options

### Option A: Merge (Recommended)

**Best for**: Projects that want k6 integrated into their existing infrastructure

**What it does**:
- Adds k6 services to existing `docker-compose.yml`
- Appends k6 documentation to existing `README.md`
- Creates `Makefile.k6` alongside existing `Makefile`
- Copies k6-specific directories (`k6/`, `grafana/`)

**Pros**:
- Single command to start all services
- Unified networking between app and k6
- Easier to manage in CI/CD

**Cons**:
- Requires editing existing docker-compose.yml
- May have port conflicts (configurable via .env)

**Setup**:
```bash
# Copy k6-specific files
cp -r <skill-path>/assets/templates/k6 ./
cp -r <skill-path>/assets/templates/grafana ./
cp <skill-path>/assets/templates/Makefile ./Makefile.k6

# Manually add k6 services to docker-compose.yml
# Manually add k6 docs to README.md
# Add k6 env vars to .env
```

**Usage**:
```bash
# Start all services (including your app)
docker-compose up -d

# Or start just k6 services
docker-compose up -d influxdb grafana

# Run tests
make -f Makefile.k6 test
```

### Option B: Separate Files

**Best for**: Projects that want k6 completely isolated or have complex existing setups

**What it does**:
- Creates `docker-compose.k6.yml` (doesn't touch existing docker-compose.yml)
- Creates `Makefile.k6` (doesn't touch existing Makefile)
- Creates `README.k6.md` (doesn't touch existing README.md)
- Copies k6-specific directories (`k6/`, `grafana/`)

**Pros**:
- Zero risk of overwriting existing files
- Easy to remove k6 later (just delete .k6 files)
- No conflicts with existing service definitions

**Cons**:
- Need to manage two docker-compose files
- Separate networks (unless explicitly connected)
- More commands to remember

**Setup**:
```bash
# Copy k6 files with .k6 suffix
cp -r <skill-path>/assets/templates/k6 ./
cp -r <skill-path>/assets/templates/grafana ./
cp <skill-path>/assets/templates/docker-compose.yml ./docker-compose.k6.yml
cp <skill-path>/assets/templates/Makefile ./Makefile.k6
cp <skill-path>/assets/templates/README.md ./README.k6.md
```

**Usage**:
```bash
# Start k6 infrastructure
docker-compose -f docker-compose.k6.yml up -d

# Or use the Makefile
make -f Makefile.k6 start

# Run tests
make -f Makefile.k6 test
```

### Option C: Fresh Project

**Best for**: New projects without existing docker-compose.yml or README.md

**What it does**:
- Copies all templates directly to project root
- No existing files to worry about

**Setup**:
```bash
cp -r <skill-path>/assets/templates/* ./
```

**Usage**:
```bash
make start
make test
```

## Using the Setup Script

For convenience, use the provided setup script which automatically detects existing files and guides you:

```bash
# From skill templates directory
bash scripts/setup.sh /path/to/your/project

# Or if already in your project directory
bash /path/to/skill/assets/templates/scripts/setup.sh
```

The script will:
1. Check for existing `docker-compose.yml`, `README.md`, and `Makefile`
2. Show you which files exist
3. Let you choose integration method
4. Copy files safely
5. Show next steps

## k6 Service Definitions

When merging (Option A), add these services to your `docker-compose.yml`:

```yaml
services:
  # ... your existing services ...
  
  # k6 Load Testing Services
  influxdb:
    image: influxdb:1.8
    container_name: k6-influxdb
    ports:
      - "${INFLUXDB_PORT:-8086}:8086"
    environment:
      - INFLUXDB_DB=${INFLUXDB_DB:-k6}
      - INFLUXDB_HTTP_AUTH_ENABLED=false
    volumes:
      - influxdb-data:/var/lib/influxdb
    networks:
      - k6-network
    healthcheck:
      test: ["CMD", "influx", "-execute", "SHOW DATABASES"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 15s

  grafana:
    image: grafana/grafana:10.2.0
    container_name: k6-grafana
    ports:
      - "${GRAFANA_PORT:-3001}:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER:-admin}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
      # Auto-load the k6 dashboard as home page
      - GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH=/etc/grafana/dashboards/k6-load-testing-results.json
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/etc/grafana/dashboards
    networks:
      - k6-network
    depends_on:
      influxdb:
        condition: service_healthy

  k6:
    image: grafana/k6:0.48.0
    container_name: k6-runner
    environment:
      - K6_OUT=influxdb=http://influxdb:8086/${INFLUXDB_DB:-k6}
      - TARGET_URL=${TARGET_URL:-https://test.k6.io}
    volumes:
      - ./k6/scripts:/scripts
      - ./k6/config:/config
    networks:
      - k6-network
    # Enable access to host services (for testing localhost APIs)
    extra_hosts:
      - "host.docker.internal:host-gateway"
    depends_on:
      - influxdb
    # Run on-demand via: docker-compose run --rm k6 run /scripts/test.js

networks:
  # ... your existing networks ...
  k6-network:
    driver: bridge

volumes:
  # ... your existing volumes ...
  influxdb-data:
    driver: local
  grafana-data:
    driver: local
```

## README.md Section Template

When merging (Option A), append this to your `README.md`:

```markdown
## Load Testing with k6

This project includes k6 load testing infrastructure for performance testing.

### Quick Start

1. Ensure k6 environment variables are set in your `.env`:
   ```bash
   TARGET_URL=https://your-api-url.com
   K6_VUS=10
   K6_DURATION=5m
   GRAFANA_PORT=3001
   INFLUXDB_PORT=8086
   ```

2. Start the testing infrastructure:
   ```bash
   make -f Makefile.k6 start
   ```

3. Run a test:
   ```bash
   make -f Makefile.k6 test
   ```

4. View results:
   - Open http://localhost:3001
   - Login: admin/admin

### Available Commands

- `make -f Makefile.k6 start` - Start InfluxDB and Grafana
- `make -f Makefile.k6 test` - Run basic load test
- `make -f Makefile.k6 test-load` - Run load test template
- `make -f Makefile.k6 test-stress` - Run stress test
- `make -f Makefile.k6 test-spike` - Run spike test
- `make -f Makefile.k6 test-soak` - Run soak test (2+ hours)
- `make -f Makefile.k6 status` - Check service status
- `make -f Makefile.k6 clean` - Stop services and remove data

### Test Types

| Test Type | Duration | Purpose |
|-----------|----------|---------|
| Load | 5-10 min | Validate normal performance |
| Stress | 15-20 min | Find capacity limits |
| Spike | 5-8 min | Handle sudden traffic bursts |
| Soak | 2-8 hours | Detect memory leaks |

See Makefile.k6 for all available commands.
```

## Environment Variables

Add these to your `.env` file:

```bash
# Required - for external APIs
TARGET_URL=https://api.example.com

# Required - for localhost APIs (see Network Configuration below)
TARGET_URL=http://host.docker.internal:3000/api

# Optional (with defaults)
K6_VUS=10                    # Number of virtual users
K6_DURATION=5m              # Test duration
GRAFANA_PORT=3001           # Grafana web interface port
INFLUXDB_PORT=8086          # InfluxDB API port
GRAFANA_ADMIN_USER=admin    # Grafana login
GRAFANA_ADMIN_PASSWORD=admin # Grafana password
INFLUXDB_DB=k6              # InfluxDB database name
```

**Important**: When testing APIs running on your local machine (localhost), you must use `host.docker.internal` instead of `localhost` because k6 runs inside a Docker container with its own network.

**For Docker Desktop (Mac/Windows):**
```bash
# If your API runs on http://localhost:3000
TARGET_URL=http://host.docker.internal:3000
```

**For Linux:**
```bash
# Use host's IP address (Docker bridge gateway)
TARGET_URL=http://172.17.0.1:3000
```

## Troubleshooting

### Issue: k6 services conflict with existing services

**Solution**: Use Option B (separate files) or change port mappings in `.env`:
```bash
GRAFANA_PORT=3002  # Instead of 3001
INFLUXDB_PORT=8087 # Instead of 8086
```

### Issue: k6 can't reach my application

**Solution**: When using Option B, k6 runs in a separate Docker network. Either:
1. Use Option A (merge) so k6 is in the same network as your app
2. Expose your app on host network and use `host.docker.internal` as the target
3. Connect the networks in docker-compose:
   ```yaml
   networks:
     k6-network:
       external: true  # Use your app's network
   ```

### Issue: Makefile.k6 commands fail

**Solution**: Check which docker-compose file is being used:
- Option A (merge): Uses `docker-compose` (default file)
- Option B (separate): Uses `docker-compose -f docker-compose.k6.yml`

The Makefile.k6 should be configured correctly by the setup script, but verify if needed.

### Issue: Grafana dashboard not showing

**Solution**:
1. Ensure dashboard file exists at `grafana/dashboards/k6-load-testing-results.json`
2. Check provisioning config: `grafana/provisioning/dashboards/default.yml`
3. Restart Grafana: `docker-compose restart grafana`
4. Check logs: `docker-compose logs grafana | grep -i dashboard`
5. Manual import: Go to http://localhost:3001/dashboard/import

### Issue: k6 can't reach localhost API on host machine

**Solution**: This is the most common issue! k6 runs in a Docker container with its own network.

**For Docker Desktop (Mac/Windows):**
```bash
# WRONG - k6 can't reach this
TARGET_URL=http://localhost:3000/api

# CORRECT - use host.docker.internal
TARGET_URL=http://host.docker.internal:3000/api
```

**For Linux:**
```bash
# Option 1: Use host IP (Docker bridge gateway)
TARGET_URL=http://172.17.0.1:3000/api

# Option 2: Add network_mode to k6 service in docker-compose.yml
network_mode: host
```

**Verify connectivity:**
```bash
# Test from k6 container to host
docker-compose run --rm k6 sh -c "wget -qO- http://host.docker.internal:3000/health || echo 'Failed to reach host'"
```

**Note**: The docker-compose.yml includes `extra_hosts` configuration to enable `host.docker.internal` resolution on most systems.

## Best Practices

1. **Always check for existing files first** before running any copy commands
2. **Use the setup script** - it handles detection and guidance automatically
3. **Backup existing files** before making changes
4. **Use version control** - commit before adding k6, so you can easily revert
5. **Test in a branch** - don't add k6 directly to main/master
6. **Document your choice** - mention in project docs which integration option you chose

## Decision Flowchart

```
Does your project have docker-compose.yml?
├── No → Use Option C (Fresh Project)
└── Yes → Do you want k6 integrated with your app?
    ├── Yes → Use Option A (Merge)
    │         └── Are there port conflicts?
    │             ├── Yes → Customize ports in .env
    │             └── No → Proceed with merge
    └── No → Use Option B (Separate)
```

## Migration from Old Setup

If you previously used `cp -r templates/* ./` and overwrote your files:

1. **Restore from git**: `git checkout -- docker-compose.yml README.md Makefile`
2. **Choose integration option** from this guide
3. **Re-add k6 safely** using the new method
4. **Commit the k6 files** to preserve them

## Summary

| Integration | Overwrites Files | Complexity | Best For |
|-------------|------------------|------------|----------|
| **A: Merge** | No* | Medium | Most projects |
| **B: Separate** | No | Low | Complex projects |
| **C: Fresh** | N/A | Low | New projects |

*Requires manual editing of existing files

## Support

- See `SKILL.md` for detailed skill usage
- See `references/test-templates.md` for test customization
- See `references/ci-cd-examples.md` for CI/CD integration
