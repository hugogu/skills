# Makefile for k6 Stress Test Suite
# Provides convenient shortcuts for common operations

.PHONY: help start stop restart status clean test test-load test-stress test-spike test-soak logs-influxdb logs-grafana export-dashboard

# Default target
help:
	@echo "k6 Stress Test Suite - Available Commands"
	@echo "=========================================="
	@echo ""
	@echo "Setup & Infrastructure:"
	@echo "  make start           Start InfluxDB and Grafana services"
	@echo "  make stop            Stop all services"
	@echo "  make restart         Restart all services"
	@echo "  make status          Show service status"
	@echo "  make clean           Stop services and remove data volumes"
	@echo ""
	@echo "Running Tests:"
	@echo "  make test            Run basic load test"
	@echo "  make test-load       Run load test template"
	@echo "  make test-stress     Run stress test template"
	@echo "  make test-spike      Run spike test template"
	@echo "  make test-soak       Run soak test template (WARNING: 2+ hours)"
	@echo "  make test-multi      Run multi-scenario test"
	@echo ""
	@echo "Utilities:"
	@echo "  make logs-influxdb   Show InfluxDB logs"
	@echo "  make logs-grafana    Show Grafana logs"
	@echo "  make cleanup-data    Remove old InfluxDB data (7 days+)"
	@echo "  make export-dashboard Export Grafana dashboards"
	@echo ""
	@echo "Environment Variables:"
	@echo "  TARGET_URL           API endpoint to test (default: https://test.k6.io)"
	@echo "  K6_VUS              Number of virtual users"
	@echo "  K6_DURATION         Test duration (e.g., 30s, 5m, 1h)"
	@echo ""
	@echo "Examples:"
	@echo "  make test TARGET_URL=https://api.example.com"
	@echo "  make test-load K6_VUS=50 K6_DURATION=5m"
	@echo ""

# Setup & Infrastructure
start:
	@echo "Starting services..."
	docker-compose up -d influxdb grafana
	@echo "Waiting for services to initialize (30s)..."
	@sleep 30
	@echo "Services ready!"
	@echo "Grafana: http://localhost:$${GRAFANA_PORT:-3000}"
	@echo "InfluxDB: http://localhost:$${INFLUXDB_PORT:-8086}"

stop:
	@echo "Stopping services..."
	docker-compose down

restart: stop start

status:
	@docker-compose ps

clean:
	@echo "Stopping services and removing data..."
	docker-compose down -v
	@echo "Cleanup complete!"

# Running Tests
test:
	@echo "Running basic load test..."
	docker-compose run --rm k6 run /scripts/examples/basic-load-test.js

test-load:
	@echo "Running load test template..."
	docker-compose run --rm k6 run /scripts/templates/load-test-template.js

test-stress:
	@echo "Running stress test template..."
	docker-compose run --rm k6 run /scripts/templates/stress-test-template.js

test-spike:
	@echo "Running spike test template..."
	docker-compose run --rm k6 run /scripts/templates/spike-test-template.js

test-soak:
	@echo "⚠️  WARNING: Soak test runs for 2+ hours"
	@read -p "Are you sure? (yes/no): " confirm && [ $$confirm = yes ]
	docker-compose run --rm k6 run /scripts/templates/soak-test-template.js

test-multi:
	@echo "Running multi-scenario test..."
	docker-compose run --rm k6 run /scripts/examples/multi-scenario-test.js

# Logs
logs-influxdb:
	docker-compose logs -f influxdb

logs-grafana:
	docker-compose logs -f grafana

# Utilities
cleanup-data:
	@echo "Removing old InfluxDB data..."
	@./scripts/cleanup-data.sh

export-dashboard:
	@echo "Exporting Grafana dashboards..."
	@./scripts/export-dashboard.sh --all

# Custom test with environment variables
test-custom:
	@if [ -z "$(SCRIPT)" ]; then \
		echo "Error: SCRIPT variable not set"; \
		echo "Usage: make test-custom SCRIPT=/scripts/my-test.js"; \
		exit 1; \
	fi
	@echo "Running custom test: $(SCRIPT)"
	docker-compose run --rm k6 run $(SCRIPT)

# Quick start - setup and run a test
quickstart: start
	@echo ""
	@echo "Running quick test..."
	docker-compose run --rm k6 run /scripts/examples/basic-load-test.js
	@echo ""
	@echo "View results at: http://localhost:$${GRAFANA_PORT:-3000}"
	@echo "Default login: admin/admin"
