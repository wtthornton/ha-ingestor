#!/bin/bash
# Stop and Remove All HA-Ingestor Containers
# Safe execution with confirmation and status checks
# DO NOT RUN without backing up data first!

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo "=================================="
echo "  HA-INGESTOR COMPLETE TEARDOWN"
echo "=================================="
echo ""
log_warning "This script will:"
echo "  1. Stop all running services"
echo "  2. Remove all containers"
echo "  3. Remove all images"
echo "  4. Remove Docker network"
echo "  5. Clean build cache"
echo ""
log_info "Data volumes will be PRESERVED by default"
echo ""

# Check if services are running
RUNNING_CONTAINERS=$(docker ps -a --filter "name=homeiq" --format "{{.Names}}" | wc -l)
log_info "Found $RUNNING_CONTAINERS homeiq containers"

if [ "$RUNNING_CONTAINERS" -eq 0 ]; then
    log_warning "No homeiq containers found!"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Aborted by user"
        exit 0
    fi
fi

# Show current status
echo ""
log_info "Current container status:"
docker ps -a --filter "name=homeiq" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || true
echo ""

# Confirmation prompt
log_warning "⚠️  IMPORTANT: Have you created backups?"
echo ""
echo "  Required backups:"
echo "    ✓ InfluxDB data: docker exec homeiq-influxdb influx backup /tmp/backup"
echo "    ✓ SQLite data: docker cp homeiq-data-api:/app/data/metadata.db ~/backup-metadata.db"
echo "    ✓ Environment: cp .env ~/backup-env"
echo ""
read -p "Have you completed backups? (yes/NO): " -r BACKUP_CONFIRM

if [ "$BACKUP_CONFIRM" != "yes" ]; then
    log_error "Backups not confirmed. Aborting for safety."
    log_info "Please create backups first!"
    exit 1
fi

echo ""
read -p "Are you SURE you want to tear down everything? (type 'yes' to continue): " -r FINAL_CONFIRM

if [ "$FINAL_CONFIRM" != "yes" ]; then
    log_info "Aborted by user"
    exit 0
fi

echo ""
log_info "Starting complete teardown..."
echo ""

# Step 1: Stop services gracefully with docker-compose
log_info "Step 1/7: Stopping services gracefully (30s timeout)..."
if [ -f "docker-compose.yml" ]; then
    docker-compose down --timeout 30 2>/dev/null || log_warning "docker-compose down failed (may not be running)"
else
    log_warning "docker-compose.yml not found, skipping graceful shutdown"
fi
log_success "Graceful shutdown complete"
echo ""

# Step 2: Force stop any remaining containers
log_info "Step 2/7: Force stopping any remaining containers..."
RUNNING=$(docker ps --filter "name=homeiq" -q)
if [ -n "$RUNNING" ]; then
    echo "$RUNNING" | xargs docker stop 2>/dev/null || true
    log_success "Stopped $(echo "$RUNNING" | wc -w) running containers"
else
    log_info "No running containers found"
fi
echo ""

# Step 3: Remove all containers
log_info "Step 3/7: Removing all homeiq containers..."
ALL_CONTAINERS=$(docker ps -a --filter "name=homeiq" -q)
if [ -n "$ALL_CONTAINERS" ]; then
    echo "$ALL_CONTAINERS" | xargs docker rm -f 2>/dev/null || true
    log_success "Removed $(echo "$ALL_CONTAINERS" | wc -w) containers"
else
    log_info "No containers to remove"
fi
echo ""

# Step 4: Remove all images
log_info "Step 4/7: Removing all homeiq images..."
ALL_IMAGES=$(docker images --filter=reference='*homeiq*' -q)
if [ -n "$ALL_IMAGES" ]; then
    echo "$ALL_IMAGES" | xargs docker rmi -f 2>/dev/null || true
    log_success "Removed $(echo "$ALL_IMAGES" | wc -w) images"
else
    log_info "No images to remove"
fi
echo ""

# Step 5: Remove network
log_info "Step 5/7: Removing Docker network..."
docker network rm homeiq-network 2>/dev/null && log_success "Network removed" || log_info "Network not found or already removed"
docker network rm homeiq-network-dev 2>/dev/null || true
echo ""

# Step 6: Clean build cache
log_info "Step 6/7: Cleaning Docker build cache..."
docker builder prune -a -f > /dev/null 2>&1
log_success "Build cache cleaned"
echo ""

# Step 7: Verify cleanup
log_info "Step 7/7: Verifying cleanup..."
echo ""

REMAINING_CONTAINERS=$(docker ps -a --filter "name=homeiq" -q | wc -l)
REMAINING_IMAGES=$(docker images --filter=reference='*homeiq*' -q | wc -l)
REMAINING_NETWORKS=$(docker network ls | grep -c "homeiq" || echo "0")

log_info "Cleanup verification:"
echo "  Containers: $REMAINING_CONTAINERS (should be 0)"
echo "  Images: $REMAINING_IMAGES (should be 0)"
echo "  Networks: $REMAINING_NETWORKS (should be 0)"
echo ""

if [ "$REMAINING_CONTAINERS" -eq 0 ] && [ "$REMAINING_IMAGES" -eq 0 ] && [ "$REMAINING_NETWORKS" -eq 0 ]; then
    log_success "✅ Complete teardown successful!"
else
    log_warning "⚠️  Some items remain - may need manual cleanup"
fi

# Show volume status
echo ""
log_info "Volume status (preserved):"
docker volume ls | grep homeiq || log_info "No homeiq volumes found"
echo ""

# Next steps
echo "=================================="
log_success "TEARDOWN COMPLETE!"
echo "=================================="
echo ""
log_info "Next steps:"
echo ""
echo "  1. Rebuild images:"
echo "     docker-compose build --no-cache --parallel"
echo ""
echo "  2. Deploy services:"
echo "     docker-compose up -d"
echo ""
echo "  3. Monitor startup:"
echo "     watch -n 2 'docker-compose ps'"
echo ""
echo "  4. Validate deployment:"
echo "     ./scripts/test-services.sh"
echo "     curl http://localhost:3000"
echo ""
log_info "Full rebuild guide: implementation/COMPLETE_SYSTEM_REBUILD_PLAN.md"
echo ""

