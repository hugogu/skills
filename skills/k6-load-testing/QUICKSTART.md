# k6 Load Testing - Quick Reference

## ⚠️ CRITICAL: Check Existing Files First!

**Before running any commands, check if these files exist:**
- `docker-compose.yml`
- `README.md`
- `Makefile`

## 🚀 Quick Setup (Use the Script)

```bash
bash /path/to/skill/assets/templates/scripts/setup.sh
```

This script automatically detects existing files and guides you through safe integration.

## 📋 Integration Options

### Option A: Merge (Recommended)
Best for: Most projects wanting integrated k6

```bash
# 1. Copy k6-specific files (safe)
cp -r <skill-path>/assets/templates/k6 ./
cp -r <skill-path>/assets/templates/grafana ./
cp <skill-path>/assets/templates/Makefile ./Makefile.k6

# 2. Add k6 services to your docker-compose.yml
#    (see SKILL.md or references/file-handling.md for service definitions)

# 3. Add k6 section to your README.md

# 4. Add to .env:
#    TARGET_URL=https://your-api.com
#    GRAFANA_PORT=3001
#    INFLUXDB_PORT=8086

# 5. Use it:
make -f Makefile.k6 start
make -f Makefile.k6 test
```

### Option B: Separate Files
Best for: Projects wanting isolated k6 setup

```bash
# Copy with .k6 suffix (doesn't touch existing files)
cp -r <skill-path>/assets/templates/k6 ./
cp -r <skill-path>/assets/templates/grafana ./
cp <skill-path>/assets/templates/docker-compose.yml ./docker-compose.k6.yml
cp <skill-path>/assets/templates/Makefile ./Makefile.k6
cp <skill-path>/assets/templates/README.md ./README.k6.md

# Setup updates Makefile.k6 to use docker-compose.k6.yml automatically

# Use it:
make -f Makefile.k6 start
make -f Makefile.k6 test
```

### Option C: Fresh Project
Best for: New projects without existing files

```bash
# Only if NO docker-compose.yml or README.md exists!
cp -r <skill-path>/assets/templates/* ./

make start
make test
```

## 🎯 Common Commands

**Merged setup (Option A):**
```bash
make -f Makefile.k6 start          # Start services
make -f Makefile.k6 test           # Run test
make -f Makefile.k6 test-load      # Load test
make -f Makefile.k6 test-stress    # Stress test
make -f Makefile.k6 test-spike     # Spike test
make -f Makefile.k6 status         # Check status
make -f Makefile.k6 clean          # Clean up
```

**Separate setup (Option B) or Fresh (Option C):**
```bash
make start
make test
make test-load
make test-stress
make test-spike
make status
make clean
```

## 🔧 Key Configuration

Add to `.env`:
```bash
TARGET_URL=https://api.example.com    # Required
K6_VUS=10                              # Virtual users
K6_DURATION=5m                         # Test duration
GRAFANA_PORT=3001                      # Grafana port
INFLUXDB_PORT=8086                     # InfluxDB port
```

**⚠️ Testing localhost APIs?**
Use `host.docker.internal` instead of `localhost`:
```bash
# If your API runs on http://localhost:3000
TARGET_URL=http://host.docker.internal:3000

# Linux users: use host IP instead
TARGET_URL=http://172.17.0.1:3000
```

**⚠️ Dev server blocking requests (403 Forbidden)?**
Modern dev servers (Vite, webpack) block non-localhost hosts. Add to your dev server config:
```javascript
// vite.config.ts
server: {
  allowedHosts: ['host.docker.internal']
}
```
Or use `--host` flag: `npm run dev -- --host`

## 🌐 Accessing Results

- **Grafana**: http://localhost:3001
- **Login**: admin/admin
- **Dashboard**: k6 Load Testing Results

## 🆘 Troubleshooting

**Dashboard not showing in Grafana?**
→ Check file exists: `ls grafana/dashboards/k6-load-testing-results.json`
→ Restart Grafana: `docker-compose restart grafana`
→ Access manually: http://localhost:3001/dashboards

**k6 can't reach localhost API?**
→ Use `host.docker.internal` instead of `localhost`:
```bash
# Wrong
TARGET_URL=http://localhost:3000/api

# Correct
TARGET_URL=http://host.docker.internal:3000/api
```
→ Test connectivity:
```bash
docker-compose run --rm k6 sh -c "wget -qO- http://host.docker.internal:3000/health"
```
→ For Linux, add to docker-compose.yml k6 service: `network_mode: host`

**Port conflicts?**
→ Change ports in `.env`:
```bash
GRAFANA_PORT=3002
INFLUXDB_PORT=8087
```

**Services not starting?**
→ Check: `make -f Makefile.k6 status`
→ View logs: `make -f Makefile.k6 logs`

## 📚 Full Documentation

- `SKILL.md` - Complete skill guide
- `references/file-handling.md` - Detailed file integration guide
- `references/test-templates.md` - Test customization
- `references/ci-cd-examples.md` - CI/CD integration

## ⚡ Decision Tree

```
Have docker-compose.yml?
├── NO → Option C (Fresh)
└── YES → Want integrated k6?
    ├── YES → Option A (Merge)
    └── NO → Option B (Separate)
```

## 🎓 Best Practices

1. ✅ Always check for existing files first
2. ✅ Use the setup script for guidance
3. ✅ Backup before making changes
4. ✅ Test in a branch, not main
5. ❌ Never run `cp -r templates/* ./` without checking!
