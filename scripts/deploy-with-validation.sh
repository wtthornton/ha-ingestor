#!/bin/bash
# Home Assistant Ingestor - Deployment Pipeline with API Key Validation
# This script ensures all API keys and tokens are validated before deployment

set -e  # Exit on any error

echo "🚀 Home Assistant Ingestor - Deployment Pipeline"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_status "Creating .env from template..."
    cp infrastructure/env.example .env
    print_warning "Please configure your .env file with valid API keys and tokens"
    exit 1
fi

# Step 1: Validate API Keys and Tokens
print_status "Step 1: Validating API keys and tokens..."
if python tests/test_api_keys.py --env-file .env; then
    print_success "All API keys and tokens are valid!"
else
    print_error "API key validation failed!"
    print_warning "Please check your .env file and ensure all tokens are valid"
    exit 1
fi

# Step 2: Backup current configuration
print_status "Step 2: Backing up current configuration..."
if [ -f ".env" ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    print_success "Configuration backed up"
fi

# Step 3: Build Docker images
print_status "Step 3: Building Docker images..."
if docker-compose build; then
    print_success "Docker images built successfully!"
else
    print_error "Docker build failed!"
    exit 1
fi

# Step 4: Start services
print_status "Step 4: Starting services..."
if docker-compose up -d; then
    print_success "Services started successfully!"
else
    print_error "Service startup failed!"
    exit 1
fi

# Step 5: Wait for services to be healthy
print_status "Step 5: Waiting for services to be healthy..."
sleep 30

# Step 6: Run comprehensive smoke tests
print_status "Step 6: Running comprehensive smoke tests..."
if python tests/smoke_tests.py --admin-url "http://localhost:8003"; then
    print_success "All smoke tests passed! System is deployment ready."
else
    print_error "Smoke tests failed! System is not deployment ready."
    print_warning "Please check the smoke test results and fix critical issues."
    exit 1
fi

# Step 7: Validate deployment
print_status "Step 7: Final deployment validation..."

# Check service health
if docker-compose ps | grep -q "unhealthy"; then
    print_warning "Some services are unhealthy. Checking logs..."
    docker-compose ps
    print_status "Checking logs for unhealthy services..."
    docker-compose logs --tail=20 $(docker-compose ps --services | xargs -I {} sh -c 'docker-compose ps {} | grep -q unhealthy && echo {}')
else
    print_success "All services are healthy!"
fi

# Test API endpoints
print_status "Testing API endpoints..."
if curl -f http://localhost:8080/api/v1/health > /dev/null 2>&1; then
    print_success "Admin API is responding!"
else
    print_warning "Admin API is not responding yet (may still be starting)"
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    print_success "Health Dashboard is responding!"
else
    print_warning "Health Dashboard is not responding yet (may still be starting)"
fi

# Final status
print_status "Deployment Summary:"
echo "==================="
docker-compose ps

print_success "Deployment completed!"
print_status "Access points:"
echo "  - Health Dashboard: http://localhost:3000"
echo "  - Admin API: http://localhost:8080"
echo "  - API Documentation: http://localhost:8080/docs"
echo "  - InfluxDB: http://localhost:8086"

print_status "To view logs: docker-compose logs -f [service-name]"
print_status "To stop services: docker-compose down"
