# K6 Load Testing - Quick Start Guide

**Note**: This README is for standalone k6 load testing setup. If you're integrating k6 into an existing project with docker-compose.yml and README.md, see Option A or B in SKILL.md instead.

## Installation (Fresh Project)

Only use this if your project doesn't have existing docker-compose.yml or README.md files:

```bash
# Copy all templates to your project root
cp -r <skill-path>/assets/templates/* ./
```

## Installation (Existing Project)

If your project already has docker-compose.yml or README.md, DO NOT use the command above. Instead:

### Option 1: Merge with existing files (Recommended)
1. Copy k6-specific files:
   ```bash
   cp -r <skill-path>/assets/templates/k6 ./
   cp -r <skill-path>/assets/templates/grafana ./
   cp <skill-path>/assets/templates/Makefile ./Makefile.k6
   ```

2. Add k6 services to your existing `docker-compose.yml` (see SKILL.md for the service definitions)

3. Add k6 documentation to your existing `README.md`

### Option 2: Use separate files
```bash
cp -r <skill-path>/assets/templates/k6 ./
cp -r <skill-path>/assets/templates/grafana ./
cp <skill-path>/assets/templates/Makefile ./Makefile.k6
cp <skill-path>/assets/templates/docker-compose.yml ./docker-compose.k6.yml
```

## Configuration

1. Set up environment variables:
   ```bash
   # Add to your existing .env file, or create a new one:
   TARGET_URL=https://your-api-url.com
   K6_VUS=10
   K6_DURATION=5m
   GRAFANA_PORT=3001
   INFLUXDB_PORT=8086
   ```

2. Start the infrastructure:
   ```bash
   # For fresh projects:
   make start
   
   # For existing projects (merged):
   make -f Makefile.k6 start
   
   # For existing projects (separate):
   docker-compose -f docker-compose.k6.yml up -d
   ```

3. Run your first test:
   ```bash
   # For fresh projects:
   make test
   
   # For existing projects:
   make -f Makefile.k6 test
   ```

4. View results:
   - Open http://localhost:3001
   - Login: admin/admin

## Directory Structure

```
.
├── docker-compose.yml        # Services configuration (or docker-compose.k6.yml)
├── Makefile                 # Common commands (or Makefile.k6)
├── .env                     # Environment variables
├── k6/
│   ├── scripts/
│   │   ├── templates/      # Test templates
│   │   ├── examples/       # Example tests
│   │   └── utils.js        # Helper functions
│   └── config/             # k6 configuration
└── grafana/                # Dashboard configuration
    ├── dashboards/
    └── provisioning/
```

## Important: Avoid Overwriting Existing Files

⚠️ **WARNING**: Never run `cp -r <skill-path>/assets/templates/* ./` if your project already has:
- `docker-compose.yml` - Will be overwritten!
- `README.md` - Will be overwritten!
- `Makefile` - Will be overwritten!

Always check for existing files first and choose the appropriate installation method.

## Next Steps

- See SKILL.md for detailed integration instructions
- Check references/ci-cd-examples.md for CI/CD integration
- Modify k6/scripts/templates/ for your specific API
- Read references/test-templates.md for test customization
