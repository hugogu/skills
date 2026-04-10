#!/bin/bash
#
# k6-load-testing-setup.sh
# Helper script to safely integrate k6 load testing into existing projects
# This script checks for existing files and provides safe integration options
#

set -e

SKILL_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT_PATH="${1:-$(pwd)}"
TARGET_DIR="${PROJECT_PATH}"

echo "K6 Load Testing Setup"
echo "===================="
echo ""
echo "Target directory: $TARGET_DIR"
echo ""

# Check if target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Target directory does not exist: $TARGET_DIR"
    exit 1
fi

cd "$TARGET_DIR"

# Check for existing files
echo "Checking for existing files..."

EXISTING_FILES=()

if [ -f "docker-compose.yml" ]; then
    EXISTING_FILES+=("docker-compose.yml")
fi

if [ -f "README.md" ]; then
    EXISTING_FILES+=("README.md")
fi

if [ -f "Makefile" ]; then
    EXISTING_FILES+=("Makefile")
fi

if [ ${#EXISTING_FILES[@]} -eq 0 ]; then
    echo "No existing files found. This is a fresh project."
    echo ""
    read -p "Proceed with fresh project setup? (y/n): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        echo "Copying all k6 load testing files..."
        cp -r "$SKILL_PATH/assets/templates/k6" ./
        cp -r "$SKILL_PATH/assets/templates/grafana" ./
        cp "$SKILL_PATH/assets/templates/Makefile" ./
        cp "$SKILL_PATH/assets/templates/docker-compose.yml" ./
        cp "$SKILL_PATH/assets/templates/README.md" ./README.k6.md
        
        echo ""
        echo "Setup complete!"
        echo ""
        echo "Next steps:"
        echo "1. Edit .env and set TARGET_URL"
        echo "2. Run: make start"
        echo "3. Run: make test"
        echo "4. Open http://localhost:3001"
    else
        echo "Setup cancelled."
    fi
    exit 0
fi

echo "Found existing files:"
for file in "${EXISTING_FILES[@]}"; do
    echo "  - $file"
done

echo ""
echo "Choose integration method:"
echo ""
echo "1) MERGE - Add k6 services to existing docker-compose.yml and sections to README.md"
echo "   (Recommended for most projects)"
echo ""
echo "2) SEPARATE - Create docker-compose.k6.yml and Makefile.k6 (keep existing files untouched)"
echo "   (Use this if you want to keep k6 completely isolated)"
echo ""
echo "3) CANCEL - Exit without making changes"
echo ""

read -p "Enter choice (1, 2, or 3): " choice

case $choice in
    1)
        echo ""
        echo "Setting up MERGE integration..."
        echo ""
        
        # Copy k6-specific directories (safe)
        echo "Copying k6 directories..."
        cp -r "$SKILL_PATH/assets/templates/k6" ./
        cp -r "$SKILL_PATH/assets/templates/grafana" ./
        
        # Copy Makefile with .k6 suffix
        echo "Creating Makefile.k6..."
        cp "$SKILL_PATH/assets/templates/Makefile" ./Makefile.k6
        
        # Show user what to add to docker-compose.yml
        echo ""
        echo "============================================"
        echo "ADD THE FOLLOWING TO YOUR docker-compose.yml"
        echo "============================================"
        echo ""
        cat << 'EOF'
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
    depends_on:
      - influxdb

networks:
  k6-network:
    driver: bridge

volumes:
  influxdb-data:
    driver: local
  grafana-data:
    driver: local
EOF
        echo ""
        echo "============================================"
        echo ""
        
        # Create a README snippet
        echo "Creating README.k6.md with documentation..."
        cat > README.k6.md << 'EOF'
# K6 Load Testing

## Quick Start

1. Add k6 services to your `docker-compose.yml` (see output above)

2. Add environment variables to your `.env`:
   ```
   TARGET_URL=https://your-api-url.com
   K6_VUS=10
   K6_DURATION=5m
   GRAFANA_PORT=3001
   INFLUXDB_PORT=8086
   ```

3. Start the infrastructure:
   ```bash
   make -f Makefile.k6 start
   ```

4. Run a test:
   ```bash
   make -f Makefile.k6 test
   ```

5. View results:
   - Open http://localhost:3001
   - Login: admin/admin

## Available Commands

```bash
make -f Makefile.k6 start          # Start InfluxDB + Grafana
make -f Makefile.k6 test           # Run basic load test
make -f Makefile.k6 test-load      # Load test
make -f Makefile.k6 test-stress    # Stress test
make -f Makefile.k6 test-spike     # Spike test
make -f Makefile.k6 test-soak      # Soak test (2+ hours)
make -f Makefile.k6 status         # Check services
make -f Makefile.k6 clean          # Remove all data
```

See SKILL.md for detailed documentation.
EOF
        
        echo ""
        echo "Setup complete!"
        echo ""
        echo "Next steps:"
        echo "1. Add the k6 services shown above to your docker-compose.yml"
        echo "2. Add k6 environment variables to your .env file"
        echo "3. Review README.k6.md for usage instructions"
        echo "4. Run: make -f Makefile.k6 start"
        echo ""
        ;;
        
    2)
        echo ""
        echo "Setting up SEPARATE integration..."
        echo ""
        
        # Copy k6-specific directories (safe)
        echo "Copying k6 directories..."
        cp -r "$SKILL_PATH/assets/templates/k6" ./
        cp -r "$SKILL_PATH/assets/templates/grafana" ./
        
        # Copy files with .k6 suffix
        echo "Creating docker-compose.k6.yml..."
        cp "$SKILL_PATH/assets/templates/docker-compose.yml" ./docker-compose.k6.yml
        
        echo "Creating Makefile.k6..."
        cp "$SKILL_PATH/assets/templates/Makefile" ./Makefile.k6
        
        echo "Creating README.k6.md..."
        cp "$SKILL_PATH/assets/templates/README.md" ./README.k6.md
        
        # Update Makefile.k6 to use the correct docker-compose file
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' 's/docker-compose /docker-compose -f docker-compose.k6.yml /g' Makefile.k6
        else
            # Linux
            sed -i 's/docker-compose /docker-compose -f docker-compose.k6.yml /g' Makefile.k6
        fi
        
        echo ""
        echo "Setup complete!"
        echo ""
        echo "Next steps:"
        echo "1. Edit .env and set TARGET_URL"
        echo "2. Run: docker-compose -f docker-compose.k6.yml up -d"
        echo "   OR:  make -f Makefile.k6 start"
        echo "3. Run: make -f Makefile.k6 test"
        echo "4. Open http://localhost:3001"
        echo ""
        echo "Note: Your existing docker-compose.yml and Makefile were NOT modified."
        echo "      k6 services run independently using docker-compose.k6.yml"
        ;;
        
    3)
        echo ""
        echo "Setup cancelled. No changes were made."
        exit 0
        ;;
        
    *)
        echo ""
        echo "Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "For more information, see SKILL.md"