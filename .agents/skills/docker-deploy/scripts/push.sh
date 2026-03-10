#!/bin/bash
#
# Push Script - Push Docker images to registry
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load environment
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    source "${PROJECT_ROOT}/.env"
    set +a
fi

REGISTRY_PREFIX="${REGISTRY_PREFIX:-localhost:5000}"
APP_VERSION="${APP_VERSION:-latest}"

# Discover services
discover_services() {
    SERVICES=()
    while IFS= read -r service; do
        if [ -n "$service" ]; then
            SERVICES+=("$service")
        fi
    done < <(grep "image:.*\${REGISTRY_PREFIX}" "${PROJECT_ROOT}/docker-compose.yml" | \
             grep -oP '^\s*\K[a-zA-Z0-9_-]+' || true)
    
    if [ ${#SERVICES[@]} -eq 0 ]; then
        log_error "No services found to push"
        exit 1
    fi
    
    log_info "Found services: ${SERVICES[*]}"
}

log_info "Pushing Docker images to registry..."
log_info "Registry: ${REGISTRY_PREFIX}"
log_info "Version: ${APP_VERSION}"

discover_services

# Push all images
for service in "${SERVICES[@]}"; do
    image="${REGISTRY_PREFIX}/$(basename "${PROJECT_ROOT}")/${service}:${APP_VERSION}"
    log_info "Pushing ${image}..."
    docker push "${image}"
done

log_info "All images pushed successfully!"
