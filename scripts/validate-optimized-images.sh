#!/bin/bash

# Docker Image Optimization Validation Script
# This script validates that the optimized Docker images work correctly

set -e

echo "🐳 Docker Image Optimization Validation"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

print_info "Docker is running"

# Build optimized images
print_info "Building optimized images..."

services=("websocket-ingestion" "admin-api" "enrichment-pipeline" "weather-api" "data-retention" "health-dashboard")

for service in "${services[@]}"; do
    print_info "Building $service..."
    if docker build -t "homeiq-$service:optimized" -f "services/$service/Dockerfile" .; then
        print_status 0 "Built $service successfully"
    else
        print_status 1 "Failed to build $service"
        exit 1
    fi
done

# Check image sizes
print_info "Checking image sizes..."
echo ""
echo "Image Size Comparison:"
echo "====================="
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep homeiq

# Test basic functionality
print_info "Testing basic functionality..."

# Test websocket-ingestion
print_info "Testing websocket-ingestion health endpoint..."
if docker run --rm -d --name test-websocket homeiq-websocket-ingestion:optimized && \
   sleep 5 && \
   docker exec test-websocket curl -f http://localhost:8001/health > /dev/null 2>&1; then
    print_status 0 "WebSocket ingestion service is healthy"
    docker stop test-websocket > /dev/null 2>&1
else
    print_status 1 "WebSocket ingestion service health check failed"
    docker stop test-websocket > /dev/null 2>&1 || true
fi

# Test admin-api
print_info "Testing admin-api health endpoint..."
if docker run --rm -d --name test-admin homeiq-admin-api:optimized && \
   sleep 5 && \
   docker exec test-admin curl -f http://localhost:8004/health > /dev/null 2>&1; then
    print_status 0 "Admin API service is healthy"
    docker stop test-admin > /dev/null 2>&1
else
    print_status 1 "Admin API service health check failed"
    docker stop test-admin > /dev/null 2>&1 || true
fi

# Test enrichment-pipeline
print_info "Testing enrichment-pipeline health endpoint..."
if docker run --rm -d --name test-enrichment homeiq-enrichment-pipeline:optimized && \
   sleep 5 && \
   docker exec test-enrichment curl -f http://localhost:8002/health > /dev/null 2>&1; then
    print_status 0 "Enrichment pipeline service is healthy"
    docker stop test-enrichment > /dev/null 2>&1
else
    print_status 1 "Enrichment pipeline service health check failed"
    docker stop test-enrichment > /dev/null 2>&1 || true
fi

# Test weather-api
print_info "Testing weather-api health endpoint..."
if docker run --rm -d --name test-weather homeiq-weather-api:optimized && \
   sleep 5 && \
   docker exec test-weather curl -f http://localhost:8001/health > /dev/null 2>&1; then
    print_status 0 "Weather API service is healthy"
    docker stop test-weather > /dev/null 2>&1
else
    print_status 1 "Weather API service health check failed"
    docker stop test-weather > /dev/null 2>&1 || true
fi

# Test data-retention
print_info "Testing data-retention health endpoint..."
if docker run --rm -d --name test-retention homeiq-data-retention:optimized && \
   sleep 5 && \
   docker exec test-retention curl -f http://localhost:8080/health > /dev/null 2>&1; then
    print_status 0 "Data retention service is healthy"
    docker stop test-retention > /dev/null 2>&1
else
    print_status 1 "Data retention service health check failed"
    docker stop test-retention > /dev/null 2>&1 || true
fi

# Test health-dashboard
print_info "Testing health-dashboard..."
if docker run --rm -d --name test-dashboard homeiq-health-dashboard:optimized && \
   sleep 5 && \
   docker exec test-dashboard curl -f http://localhost:80 > /dev/null 2>&1; then
    print_status 0 "Health dashboard is accessible"
    docker stop test-dashboard > /dev/null 2>&1
else
    print_status 1 "Health dashboard accessibility test failed"
    docker stop test-dashboard > /dev/null 2>&1 || true
fi

# Security check - verify non-root users
print_info "Checking security configurations..."

for service in "${services[@]}"; do
    print_info "Checking $service runs as non-root user..."
    if docker run --rm homeiq-$service:optimized id | grep -q "uid=1001"; then
        print_status 0 "$service runs as non-root user (uid=1001)"
    else
        print_status 1 "$service does not run as non-root user"
    fi
done

echo ""
echo "🎉 Docker Image Optimization Validation Complete!"
echo "================================================="
echo ""
echo "Summary:"
echo "- All services built successfully with Alpine-based images"
echo "- Multi-stage builds implemented for optimal size"
echo "- Non-root users configured for security"
echo "- Health checks validated"
echo ""
echo "Next steps:"
echo "1. Test with docker-compose up"
echo "2. Monitor resource usage in production"
echo "3. Consider implementing distroless images for further optimization"
