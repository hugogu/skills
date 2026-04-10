---
name: k6-load-testing
description: |
  **USE THIS SKILL** when the user wants to set up API load testing, performance testing, or stress testing for their project. This includes requests like "帮我设置压力测试", "我想测试API性能", "create load tests for my API", "setup k6 testing", "performance test my endpoints", or any mention of load testing, stress testing, spike testing, or soak testing infrastructure.
  
  **ALSO USE** when the user mentions k6, Grafana, InfluxDB, Docker Compose testing stack, or needs to validate API performance under load.
  
  This skill provides a complete Docker-based load testing infrastructure with k6 + InfluxDB + Grafana, including templates for load tests, stress tests, spike tests, and soak tests.
---

# K6 Load Testing Skill

Set up a complete, production-ready load testing infrastructure for any API project using k6, InfluxDB, and Grafana via Docker Compose.

## What This Skill Provides

- **Complete Testing Stack**: k6 (load generator) + InfluxDB (metrics storage) + Grafana (visualization)
- **Four Test Types**: Load test, stress test, spike test, and soak test templates
- **Zero Configuration**: Works out of the box with Docker Compose
- **CI/CD Ready**: Pre-configured integrations for GitHub Actions, GitLab CI, Jenkins, and more
- **Real-time Monitoring**: Grafana dashboards with live metrics during test execution

## Quick Start

When the user wants to set up load testing:

1. **Initialize the testing infrastructure** in their project (see Step 1 below for safe file handling)

2. **Configure the target API**:
   - Ask user for their API base URL
   - Update `.env` file with TARGET_URL

3. **Choose test type** based on their needs:
   - **Load Test**: Normal traffic validation (minutes)
   - **Stress Test**: Find breaking points (20 min)
   - **Spike Test**: Sudden traffic bursts (8 min)
   - **Soak Test**: Memory leak detection (2+ hours)

4. **Run the test**:
   ```bash
   make start     # Start InfluxDB + Grafana
   make test      # Run basic load test
   ```

5. **View results**:
   - Open http://localhost:3001 (admin/admin)
   - Real-time metrics in Grafana dashboard

## Workflow

### Step 1: Initialize Infrastructure

**IMPORTANT: Check for existing files first!** Before copying, check if these files exist in the target directory:
- `docker-compose.yml`
- `README.md`

#### Option A: Merge with existing docker-compose.yml (Recommended)

If the project already has a `docker-compose.yml`:

1. Copy k6-specific files (these don't conflict):
   ```bash
   # Copy only k6-specific directories and Makefile
   cp -r <skill-path>/assets/templates/k6 ./
   cp -r <skill-path>/assets/templates/grafana ./
   cp <skill-path>/assets/templates/Makefile ./Makefile.k6
   ```

2. Merge the k6 services into existing `docker-compose.yml` by adding these services:

   ```yaml
   # Add to existing docker-compose.yml
   services:
     # ... existing services ...
     
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
          - INFLUXDB_DB=${INFLUXDB_DB:-k6}
          # Auto-load the k6 dashboard as home
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
     # ... existing networks ...
     k6-network:
       driver: bridge
   
   volumes:
     # ... existing volumes ...
     influxdb-data:
       driver: local
     grafana-data:
       driver: local
   ```

3. Add k6 documentation to existing README.md:

   Append to `README.md`:
   ```markdown
   ## Load Testing with k6
   
   This project includes k6 load testing infrastructure.
   
   ### Quick Start
   
   1. Configure environment:
      ```bash
      # Add to your .env file:
      TARGET_URL=https://your-api-url.com
      K6_VUS=10
      K6_DURATION=5m
      GRAFANA_PORT=3001
      INFLUXDB_PORT=8086
      ```
   
   2. Start testing infrastructure:
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
   
   See Makefile.k6 for more commands.
   ```

#### Option B: Use separate docker-compose file

If you prefer to keep k6 services separate:

1. Copy k6 infrastructure:
   ```bash
   cp -r <skill-path>/assets/templates/k6 ./
   cp -r <skill-path>/assets/templates/grafana ./
   cp <skill-path>/assets/templates/Makefile ./Makefile.k6
   cp <skill-path>/assets/templates/docker-compose.yml ./docker-compose.k6.yml
   ```

2. Create README.k6.md with standalone documentation:
   ```bash
   cp <skill-path>/assets/templates/README.md ./README.k6.md
   ```

3. Use separate compose commands:
   ```bash
   docker-compose -f docker-compose.k6.yml up -d
   make -f Makefile.k6 start
   ```

#### Option C: Fresh project (no existing files)

If the project doesn't have docker-compose.yml or README.md:

```bash
cp -r <skill-path>/assets/templates/* ./
```

### Step 2: Configure Target API

Read the environment configuration and guide user to create/update `.env`:

```bash
# Required - for external APIs
TARGET_URL=https://api.example.com

# Required - for localhost APIs (see Network Configuration below)
TARGET_URL=http://host.docker.internal:8080/api

# Optional customizations
K6_VUS=10                    # Virtual users
K6_DURATION=5m              # Test duration
GRAFANA_PORT=3001           # Grafana port
INFLUXDB_PORT=8086          # InfluxDB port
```

**Note**: If using Option A (merged docker-compose), add these variables to the existing `.env` file. If the project doesn't have a `.env` file, create one.

#### Network Configuration for Localhost APIs

**Critical**: When testing APIs running on your local machine (localhost), k6 runs inside a Docker container with its own network. To access host services:

**For Docker Desktop (Mac/Windows):**
Use `host.docker.internal` instead of `localhost`:
```bash
# If your API runs on http://localhost:3000
TARGET_URL=http://host.docker.internal:3000

# If your API runs on a specific path
TARGET_URL=http://host.docker.internal:5174/api/endpoint
```

**For Linux:**
Use the host's IP address or add network mode:
```bash
# Option 1: Use host network mode (add to docker-compose.yml k6 service)
network_mode: host

# Option 2: Use host's IP address
TARGET_URL=http://172.17.0.1:3000  # Docker bridge gateway
```

**The docker-compose.yml already includes:**
```yaml
k6:
  extra_hosts:
    - "host.docker.internal:host-gateway"
```

This enables `host.docker.internal` resolution on most systems.

**Verify connectivity before testing:**
```bash
# Test from k6 container to host
docker-compose run --rm k6 curl http://host.docker.internal:3000/health
```

#### Dev Server Security (Vite, webpack, etc.)

**Critical**: Modern frontend dev servers (Vite 5+, webpack, etc.) have security features that block requests from non-localhost hosts by default. This causes "403 Forbidden - Blocked request" errors when k6 tries to access `host.docker.internal`.

**Symptom:**
```
Status: 403 Forbidden
Body: Blocked request. This host ("host.docker.internal") is not allowed.
```

**Fix for Vite (vite.config.ts):**
```typescript
export default defineConfig({
  // ... other config
  server: {
    // Allow k6 container to access the dev server
    allowedHosts: ['host.docker.internal'],
    // Or allow all hosts (less secure, only for testing)
    // allowedHosts: true,
  },
})
```

**Fix for webpack (webpack.config.js):**
```javascript
module.exports = {
  // ... other config
  devServer: {
    // Allow k6 container to access the dev server
    allowedHosts: ['host.docker.internal'],
    // Or disable host check (less secure, only for testing)
    // disableHostCheck: true,
  },
}
```

**Fix for Vue CLI (vue.config.js):**
```javascript
module.exports = {
  devServer: {
    allowedHosts: ['host.docker.internal'],
  },
}
```

**Important:** After updating the config, restart your dev server for changes to take effect.

### Step 3: Generate Test Script

Based on user's API endpoints, generate a test script using templates:

**For simple load testing**:
- Use `k6/scripts/templates/load-test-template.js`
- Configure endpoints, HTTP methods, and payloads

**For comprehensive testing**:
- Generate multiple test scripts (load + stress + spike)
- Each targeting different scenarios

### Step 4: Run and Monitor

Guide user through (adjust commands based on your setup):

**For Option A (merged)**:
```bash
make -f Makefile.k6 start    # Start infrastructure
make -f Makefile.k6 test     # Run tests
docker-compose ps            # Check status
```

**For Option B (separate)**:
```bash
docker-compose -f docker-compose.k6.yml up -d
make -f Makefile.k6 test
```

**For Option C (fresh)**:
```bash
make start     # Start infrastructure
make test      # Run tests
```

Open Grafana to view real-time results, then clean up when done.

## Test Types Guide

Ask the user what they want to achieve:

| Goal | Test Type | Duration | Use Case |
|------|-----------|----------|----------|
| Validate normal performance | Load Test | 5-10 min | Pre-release validation |
| Find capacity limits | Stress Test | 15-20 min | Capacity planning |
| Handle traffic spikes | Spike Test | 5-8 min | Flash sales/events |
| Detect memory leaks | Soak Test | 2-8 hours | Long-term stability |

## CI/CD Integration

Offer to set up automated testing in their CI pipeline:

- **GitHub Actions**: `.github/workflows/performance.yml`
- **GitLab CI**: `.gitlab-ci.yml`
- **Jenkins**: `Jenkinsfile`
- **Azure DevOps**: `azure-pipelines.yml`

Read `references/ci-cd-examples.md` for ready-to-use configurations.

## Common Commands

**For merged setup (Option A)**:
```bash
make -f Makefile.k6 start          # Start InfluxDB + Grafana
make -f Makefile.k6 test           # Run basic load test
make -f Makefile.k6 test-load      # Load test with custom config
make -f Makefile.k6 test-stress    # Stress test
make -f Makefile.k6 test-spike     # Spike test
make -f Makefile.k6 test-soak      # Soak test (2+ hours)
make -f Makefile.k6 status         # Check services
make -f Makefile.k6 clean          # Remove all data
make -f Makefile.k6 logs           # View service logs
```

**For separate setup (Option B)** or **fresh setup (Option C)**:
```bash
make start          # Start InfluxDB + Grafana
make test           # Run basic load test
make test-load      # Load test with custom config
make test-stress    # Stress test
make test-spike     # Spike test
make test-soak      # Soak test (2+ hours)
make status         # Check services
make clean          # Remove all data
make logs           # View service logs
```

## Customization Points

### Authentication
If API requires auth, use helpers from `k6/scripts/utils.js`:

```javascript
import { bearerAuth, basicAuth, apiKeyAuth } from './utils.js';

// Bearer token
const headers = bearerAuth('your-token-here');

// Basic auth
const headers = basicAuth('username', 'password');

// API Key
const headers = apiKeyAuth('X-API-Key', 'your-key');
```

### Custom Thresholds
Edit `k6/config/common.json`:

```json
{
  "thresholds": {
    "http_req_duration": ["p(95)<500"],
    "http_req_failed": ["rate<0.01"]
  }
}
```

### Multiple Endpoints
Create scenarios in test script:

```javascript
export const options = {
  scenarios: {
    read: {
      executor: 'constant-vus',
      vus: 10,
      duration: '5m',
      exec: 'readTest'
    },
    write: {
      executor: 'constant-vus',
      vus: 5,
      duration: '5m',
      exec: 'writeTest'
    }
  }
};
```

## Troubleshooting

**Issue**: k6 gets "403 Forbidden - Blocked request" from dev server
- **Fix**: Dev servers (Vite, webpack) block non-localhost hosts by default. Add `allowedHosts` to your dev server config:
  ```javascript
  // vite.config.ts
  server: {
    allowedHosts: ['host.docker.internal']
  }
  ```
- **Alternative**: Use `--host` flag to allow all hosts (less secure):
  ```bash
  npm run dev -- --host
  ```
- **Note**: Restart dev server after config changes

**Issue**: Makefile.k6 commands don't work
- **Fix**: Update Makefile.k6 to use correct docker-compose command:
  - For Option A: Keep `docker-compose` (uses default docker-compose.yml)
  - For Option B: Change to `docker-compose -f docker-compose.k6.yml`

**Issue**: Grafana dashboard not showing / "No dashboards"
- **Fix**: 
  1. Check dashboard file exists: `ls grafana/dashboards/k6-load-testing-results.json`
  2. Restart Grafana: `docker-compose restart grafana`
  3. Check Grafana logs: `docker-compose logs grafana | grep -i dashboard`
  4. Dashboard should auto-provision from `grafana/provisioning/dashboards/default.yml`
  5. Access manually: http://localhost:3001/dashboards

**Issue**: k6 can't connect to localhost API on host
- **Fix**: Use `host.docker.internal` instead of `localhost` in TARGET_URL:
  ```bash
  # Wrong - k6 can't reach host localhost
  TARGET_URL=http://localhost:3000/api
  
  # Correct - use host.docker.internal
  TARGET_URL=http://host.docker.internal:3000/api
  ```
- **Fix for Linux**: Add `network_mode: host` to k6 service in docker-compose.yml, or use host IP
- **Verify**: Test connectivity from k6 container:
  ```bash
  docker-compose run --rm k6 sh -c "wget -qO- http://host.docker.internal:3000/health || echo 'Cannot reach host'"
  ```

**Issue**: Grafana shows "No data"
- **Fix**: Ensure InfluxDB is healthy (`make -f Makefile.k6 status`) and tests are running

**Issue**: k6 can't connect to target API
- **Fix**: Check `TARGET_URL` in `.env`, verify network connectivity

**Issue**: Tests fail immediately
- **Fix**: Check if API requires authentication, update headers in test script

**Issue**: Port conflicts
- **Fix**: Change ports in `.env` (GRAFANA_PORT, INFLUXDB_PORT)

## Best Practices

1. **Start small**: Begin with 10 VU load test before scaling up
2. **Use staging**: Test against staging environment first
3. **Monitor resources**: Watch CPU/memory on both test runner and target API
4. **Set thresholds**: Define acceptable performance criteria before testing
5. **Baseline first**: Run tests against current version before changes
6. **Automate**: Add to CI/CD to catch performance regressions
7. **Don't overwrite**: Always check for existing files before initializing

## File Reference

- `SKILL.md` - This file
- `references/test-templates.md` - Detailed template usage
- `references/ci-cd-examples.md` - CI/CD configuration examples
- `references/advanced-scenarios.md` - Complex testing scenarios
- `assets/templates/` - Ready-to-use template files

### Template Files Structure

```
assets/templates/
├── docker-compose.yml          # k6 services (influxdb, grafana, k6)
├── Makefile                   # k6-specific commands
├── README.md                  # Standalone documentation
├── k6/
│   ├── scripts/
│   │   ├── templates/         # Test templates
│   │   ├── examples/          # Example tests
│   │   └── utils.js           # Helper functions
│   └── config/                # k6 configuration
└── grafana/                   # Dashboard provisioning
    ├── dashboards/
    └── provisioning/
```

## Implementation Checklist

When implementing this skill:

- [ ] Check for existing `docker-compose.yml`
- [ ] Check for existing `README.md`
- [ ] Check for existing `Makefile`
- [ ] Choose integration strategy (merge, separate, or fresh)
- [ ] Copy k6-specific directories (k6/, grafana/)
- [ ] Handle docker-compose.yml appropriately
- [ ] Handle README.md appropriately  
- [ ] Handle Makefile appropriately (rename to Makefile.k6 if needed)
- [ ] Configure TARGET_URL in .env
- [ ] Test the setup with `make start`
- [ ] Verify Grafana is accessible
- [ ] Run a test to confirm data flow
