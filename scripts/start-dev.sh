#!/bin/bash

# Development Environment Startup Script
# This script starts the development environment

set -e

echo "Starting HA Ingestor Development Environment..."
echo "=============================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Running setup script..."
    ./scripts/setup-env.sh
    echo ""
fi

# Start development environment
echo "Starting development environment with docker-compose.dev.yml..."
docker-compose -f docker-compose.dev.yml up --build

echo "Development environment started!"
echo ""
echo "Services available at:"
echo "- Admin API: http://localhost:8000"
echo "- InfluxDB: http://localhost:8086"
echo "- Health checks: http://localhost:8000/health"
echo ""
echo "To view logs, run: ./scripts/view-logs.sh"
echo "To stop services, run: docker-compose -f docker-compose.dev.yml down"
