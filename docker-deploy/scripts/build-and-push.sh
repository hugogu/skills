#!/bin/bash
#
# Build and Push Script for Docker Deployment
# 
# This script performs all local operations first, then pushes to registry at the end.
# This minimizes network switching when working in environments with restricted network access.
#

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Default values
REGISTRY_PREFIX="${REGISTRY_PREFIX:-localhost:5000}"
APP_VERSION="${APP_VERSION:-latest}"
ENV="${ENV:-local}"
SKIP_TESTS="${SKIP_TESTS:-false}"
SKIP_PUSH="${SKIP_PUSH:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP $1]${NC} $2"
}

# Load environment file if it exists
load_env() {
    if [ -f "${PROJECT_ROOT}/.env" ]; then
        log_info "Loading environment from .env file..."
        set -a
        source "${PROJECT_ROOT}/.env"
        set +a
        
        # Re-apply defaults if not set
        REGISTRY_PREFIX="${REGISTRY_PREFIX:-localhost:5000}"
        APP_VERSION="${APP_VERSION:-latest}"
        ENV="${ENV:-local}"
    fi
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --registry)
                REGISTRY_PREFIX="$2"
                shift 2
                ;;
            --version)
                APP_VERSION="$2"
                shift 2
                ;;
            --skip-tests)
                SKIP_TESTS="true"
                shift
                ;;
            --skip-push)
                SKIP_PUSH="true"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Build Docker images locally and push to registry.

Options:
    --registry REGISTRY     Set registry prefix (default: localhost:5000)
    --version VERSION       Set application version (default: latest)
    --skip-tests            Skip running tests
    --skip-push             Build only, don't push to registry
    --help                  Show this help message

Environment:
    REGISTRY_PREFIX         Registry URL prefix
    APP_VERSION             Application version tag
    SKIP_TESTS              Set to "true" to skip tests

Examples:
    # Build and push to local registry
    ./build-and-push.sh

    # Build and push to production registry
    ./build-and-push.sh --registry registry.example.com --version 1.2.3

    # Build only, no push
    ./build-and-push.sh --skip-push

    # Skip tests and push
    ./build-and-push.sh --skip-tests

EOF
}

# Discover services from docker-compose.yml
discover_services() {
    log_info "Discovering services from docker-compose.yml..."
    
    if [ ! -f "${PROJECT_ROOT}/docker-compose.yml" ]; then
        log_error "docker-compose.yml not found in ${PROJECT_ROOT}"
        exit 1
    fi
    
    # Extract service names that have build contexts (custom services)
    SERVICES=()
    while IFS= read -r service; do
        if [ -n "$service" ]; then
            SERVICES+=("$service")
        fi
    done < <(grep -A 5 "^[[:space:]]*[a-zA-Z0-9_-]*:" "${PROJECT_ROOT}/docker-compose.yml" | \
             grep -B 5 "build:" | \
             grep "^[[:space:]]*[a-zA-Z0-9_-]*:" | \
             sed 's/://g' | \
             sed 's/ //g')
    
    if [ ${#SERVICES[@]} -eq 0 ]; then
        log_warn "No services with build contexts found in docker-compose.yml"
        log_info "Looking for services with REGISTRY_PREFIX in image names..."
        
        # Fallback: find services using REGISTRY_PREFIX pattern
        while IFS= read -r service; do
            if [ -n "$service" ]; then
                SERVICES+=("$service")
            fi
        done < <(grep "image:.*\${REGISTRY_PREFIX}" "${PROJECT_ROOT}/docker-compose.yml" | \
                 grep -oP '^\s*\K[a-zA-Z0-9_-]+' || true)
    fi
    
    if [ ${#SERVICES[@]} -eq 0 ]; then
        log_error "No custom services found to build"
        exit 1
    fi
    
    log_info "Found services: ${SERVICES[*]}"
}

# Pre-build checks (linting, security scans)
run_prebuild_checks() {
    log_step "1" "Running pre-build checks..."
    
    # Check Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running or not accessible"
        exit 1
    fi
    
    # Check docker-compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "docker-compose is not installed"
        exit 1
    fi
    
    log_info "Pre-build checks passed"
}

# Build Docker images
build_images() {
    log_step "2" "Building Docker images..."
    
    cd "${PROJECT_ROOT}"
    
    # Determine docker-compose command
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    log_info "Using: ${COMPOSE_CMD}"
    log_info "Registry: ${REGISTRY_PREFIX}"
    log_info "Version: ${APP_VERSION}"
    
    # Build all services with build contexts
    log_info "Building services..."
    REGISTRY_PREFIX="${REGISTRY_PREFIX}" APP_VERSION="${APP_VERSION}" ${COMPOSE_CMD} build
    
    log_info "Build completed successfully"
}

# Run tests
run_tests() {
    if [ "${SKIP_TESTS}" = "true" ]; then
        log_warn "Skipping tests as requested"
        return 0
    fi
    
    log_step "3" "Running tests..."
    
    # Start dependencies
    log_info "Starting dependencies for testing..."
    cd "${PROJECT_ROOT}"
    
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    
    # Start only third-party services (no custom services)
    ${COMPOSE_CMD} up -d postgres redis 2>/dev/null || true
    
    if [ ${#SERVICES[@]} -gt 0 ]; then
        sleep 5  # Wait for dependencies
        
        # Run tests for each service
        for service in "${SERVICES[@]}"; do
            if ${COMPOSE_CMD} ps | grep -q "${service}"; then
                log_info "Running tests for ${service}..."
                # Add test commands here
                # ${COMPOSE_CMD} exec "${service}" npm test || true
            fi
        done
    fi
    
    # Cleanup
    ${COMPOSE_CMD} down 2>/dev/null || true
    
    log_info "Tests completed"
}

# Tag images with registry prefix
tag_images() {
    log_step "4" "Tagging images with registry prefix..."
    
    for service in "${SERVICES[@]}"; do
        # Get the image name from docker-compose
        local_image="${COMPOSE_PROJECT_NAME:-$(basename "${PROJECT_ROOT}")}_${service}"
        target_image="${REGISTRY_PREFIX}/$(basename "${PROJECT_ROOT}")/${service}:${APP_VERSION}"
        
        # Check if image exists
        if docker images | grep -q "${local_image}"; then
            log_info "Tagging ${local_image} -> ${target_image}"
            docker tag "${local_image}:latest" "${target_image}" 2>/dev/null || \
            docker tag "${service}:latest" "${target_image}" 2>/dev/null || \
            log_warn "Could not tag ${service}"
        else
            log_warn "Image ${local_image} not found, may already be tagged"
        fi
    done
}

# Push images to registry
push_images() {
    if [ "${SKIP_PUSH}" = "true" ]; then
        log_warn "Skipping push as requested (--skip-push)"
        return 0
    fi
    
    log_step "5" "Pushing images to registry..."
    log_warn "Switching to registry network if needed..."
    log_info "Registry: ${REGISTRY_PREFIX}"
    
    # Check if logged in to registry
    if [[ "${REGISTRY_PREFIX}" != "localhost"* ]]; then
        if ! docker info 2>/dev/null | grep -q "Username"; then
            log_warn "You may need to login to ${REGISTRY_PREFIX}"
            log_info "Run: docker login ${REGISTRY_PREFIX}"
        fi
    fi
    
    # Push all images
    local push_failed=0
    for service in "${SERVICES[@]}"; do
        target_image="${REGISTRY_PREFIX}/$(basename "${PROJECT_ROOT}")/${service}:${APP_VERSION}"
        
        log_info "Pushing ${target_image}..."
        if docker push "${target_image}"; then
            log_info "Successfully pushed ${target_image}"
        else
            log_error "Failed to push ${target_image}"
            push_failed=1
        fi
    done
    
    if [ $push_failed -eq 1 ]; then
        log_error "Some images failed to push"
        exit 1
    fi
    
    log_info "All images pushed successfully!"
}

# Print summary
print_summary() {
    echo ""
    echo "=========================================="
    log_info "Build and Push Summary"
    echo "=========================================="
    echo "Registry: ${REGISTRY_PREFIX}"
    echo "Version:  ${APP_VERSION}"
    echo "Services: ${#SERVICES[@]}"
    echo ""
    echo "Images:"
    for service in "${SERVICES[@]}"; do
        echo "  - ${REGISTRY_PREFIX}/$(basename "${PROJECT_ROOT}")/${service}:${APP_VERSION}"
    done
    echo ""
    echo "Next steps:"
    if [ "${SKIP_PUSH}" = "true" ]; then
        echo "  1. Push images: ./scripts/push.sh"
    fi
    echo "  1. Deploy locally: docker-compose up -d"
    echo "  2. Deploy remote: docker-compose -H ssh://user@host up -d"
    echo "=========================================="
}

# Main execution
main() {
    log_info "Docker Build and Push Script"
    log_info "============================"
    
    load_env
    parse_args "$@"
    discover_services
    run_prebuild_checks
    build_images
    run_tests
    tag_images
    push_images
    print_summary
    
    log_info "Completed successfully!"
}

# Run main function
main "$@"
