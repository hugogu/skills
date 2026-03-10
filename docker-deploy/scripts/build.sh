#!/bin/bash
#
# Build Script - Build Docker images locally
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Load environment
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a
    source "${PROJECT_ROOT}/.env"
    set +a
fi

REGISTRY_PREFIX="${REGISTRY_PREFIX:-localhost:5000}"
APP_VERSION="${APP_VERSION:-latest}"

cd "${PROJECT_ROOT}"

log_info "Building Docker images..."
log_info "Registry: ${REGISTRY_PREFIX}"
log_info "Version: ${APP_VERSION}"

# Use docker compose (v2) if available, fallback to docker-compose
if docker compose version &> /dev/null; then
    REGISTRY_PREFIX="${REGISTRY_PREFIX}" APP_VERSION="${APP_VERSION}" docker compose build
else
    REGISTRY_PREFIX="${REGISTRY_PREFIX}" APP_VERSION="${APP_VERSION}" docker-compose build
fi

log_info "Build completed successfully!"
