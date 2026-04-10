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

1. **Initialize the testing infrastructure** in their project:
   ```bash
   # Copy all necessary files to the project
   cp -r <skill-path>/assets/templates/* ./
   ```

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

Ask the user which directory to initialize (usually project root). Then copy these files:

```
docker-compose.yml    # Services orchestration
Makefile             # Common commands
.env.example         # Configuration template
k6/
  scripts/
    templates/       # Test script templates
    utils.js         # Shared utilities
  config/            # Environment configs
grafana/             # Dashboard provisioning
scripts/             # Helper scripts
```

### Step 2: Configure Target API

Read the `.env.example` file and guide user to create `.env`:

```bash
# Required
TARGET_URL=https://api.example.com

# Optional customizations
K6_VUS=10                    # Virtual users
K6_DURATION=5m              # Test duration
GRAFANA_PORT=3001           # Grafana port
```

### Step 3: Generate Test Script

Based on user's API endpoints, generate a test script using templates:

**For simple load testing**:
- Use `load-test-template.js`
- Configure endpoints, HTTP methods, and payloads

**For comprehensive testing**:
- Generate multiple test scripts (load + stress + spike)
- Each targeting different scenarios

### Step 4: Run and Monitor

Guide user through:
1. `make start` - Start infrastructure
2. `make test` or `make test-load` - Run tests
3. Open Grafana to view real-time results
4. `make stop` - Clean up when done

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
If API requires auth, use helpers from `utils.js`:

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

**Issue**: Grafana shows "No data"
- **Fix**: Ensure InfluxDB is healthy (`make status`) and tests are running

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

## File Reference

- `SKILL.md` - This file
- `references/test-templates.md` - Detailed template usage
- `references/ci-cd-examples.md` - CI/CD configuration examples
- `references/advanced-scenarios.md` - Complex testing scenarios
- `assets/templates/` - Ready-to-use template files
