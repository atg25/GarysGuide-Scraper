#!/bin/bash
# Phase 2 Staging Deployment Script
# Purpose: Build and deploy PyPack MCP server to staging environment
# Usage: bash scripts/deploy_staging.sh [build|deploy|test|teardown]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMMAND="${1:-build}"
STAGING_ENV_FILE="${PROJECT_ROOT}/.env.staging"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# Step 1: Build
build_staging_image() {
    log_info "Building MCP server staging Docker image..."
    docker build \
        -f "$PROJECT_ROOT/Dockerfile.mcp-staging" \
        -t "garys-events-mcp:staging" \
        "$PROJECT_ROOT"
    log_info "Build complete: garys-events-mcp:staging"
}

# Step 2: Deploy
deploy_staging_environment() {
    log_info "Deploying staging environment..."
    
    if [ ! -f "$STAGING_ENV_FILE" ]; then
        log_warn "Staging env file not found at $STAGING_ENV_FILE"
        log_info "Creating default .env.staging..."
        cat > "$STAGING_ENV_FILE" <<'EOF'
# Staging Environment Configuration
GARYS_EVENTS_MCP_ENABLED=true
GARYS_EVENTS_REST_API_BASE_URL=http://localhost:9001
GARYS_EVENTS_REST_API_TIMEOUT_MS=5000
GARYS_EVENTS_MCP_FAIL_OPEN=true
EOF
        log_info "Created .env.staging - update as needed before deploying"
    fi
    
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.staging.yml up -d
    log_info "Staging environment deployed"
    docker-compose -f docker-compose.staging.yml ps
}

# Step 3: Validate
test_staging_deployment() {
    log_info "Testing staging MCP server..."
    
    # Test 1: Check if container is running
    if ! docker ps | grep -q garys-events-mcp-staging; then
        log_error "Staging container not running"
    fi
    log_info "✓ Container running"
    
    # Test 2: Validate MCP contract (ListTools)
    log_info "Testing MCP ListTools contract..."
    echo '{"method":"ListTools","params":{}}' | \
        docker exec -i garys-events-mcp-staging python -m garys_nyc_events.mcp.server 2>/dev/null | \
        python -m json.tool | grep -q "garys_events.query_events" || log_error "ListTools contract failed"
    log_info "✓ ListTools contract validated"
    
    # Test 3: Validate MCP contract (CallTool with invalid args should return error, not crash)
    log_info "Testing MCP CallTool error contract..."
    echo '{"method":"CallTool","params":{"name":"garys_events.query_events","arguments":{"limit":"invalid"}}}' | \
        docker exec -i garys-events-mcp-staging python -m garys_nyc_events.mcp.server 2>/dev/null | \
        python -m json.tool | grep -q "ok" || log_error "CallTool error contract failed"
    log_info "✓ CallTool contract validated"
    
    log_info "All staging tests passed ✓"
}

# Step 4: Teardown
teardown_staging() {
    log_info "Tearing down staging environment..."
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.staging.yml down -v
    log_info "Staging environment torn down"
}

# Step 5: Status
show_status() {
    log_info "Staging environment status:"
    cd "$PROJECT_ROOT"
    docker-compose -f docker-compose.staging.yml ps
    log_info ""
    log_info "To debug MCP server:"
    log_info "  docker logs garys-events-mcp-staging"
    log_info "  docker exec -it garys-events-mcp-staging bash"
}

# Route commands
case "$COMMAND" in
    build)
        build_staging_image
        ;;
    deploy)
        build_staging_image
        deploy_staging_environment
        ;;
    test)
        test_staging_deployment
        ;;
    teardown)
        teardown_staging
        ;;
    status)
        show_status
        ;;
    full)
        build_staging_image
        deploy_staging_environment
        test_staging_deployment
        show_status
        ;;
    *)
        log_error "Unknown command: $COMMAND\n\nUsage: $(basename "$0") {build|deploy|test|teardown|status|full}"
        ;;
esac
