# K6 Load Testing - Quick Start Guide

## Installation

1. Copy the templates to your project:
```bash
cp -r <skill-path>/assets/templates/* ./
```

2. Configure your environment:
```bash
cp .env.example .env
# Edit .env and set TARGET_URL to your API
```

3. Start the infrastructure:
```bash
make start
```

4. Run your first test:
```bash
make test
```

5. View results:
- Open http://localhost:3000
- Login: admin/admin

## Directory Structure

```
.
├── docker-compose.yml     # Services configuration
├── Makefile              # Common commands
├── .env                  # Environment variables
├── k6/
│   ├── scripts/
│   │   ├── templates/    # Test templates
│   │   └── utils.js      # Helper functions
│   └── config/           # k6 configuration
└── grafana/              # Dashboard configuration
```

## Next Steps

- See SKILL.md for detailed usage
- Check references/ci-cd-examples.md for CI/CD integration
- Modify k6/scripts/templates/ for your specific API
