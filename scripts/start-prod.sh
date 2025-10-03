#!/bin/bash

# Production Environment Startup Script
# This script starts the production environment

set -e

echo "Starting HA Ingestor Production Environment..."
echo "=============================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it from infrastructure/env.example"
    echo "Run: cp infrastructure/env.example .env"
    echo "Then edit .env with your production values"
    exit 1
fi

# Validate environment variables
echo "Validating environment configuration..."
source .env

required_vars=(
    "HOME_ASSISTANT_URL"
    "HOME_ASSISTANT_TOKEN"
    "INFLUXDB_USERNAME"
    "INFLUXDB_PASSWORD"
    "INFLUXDB_ORG"
    "INFLUXDB_BUCKET"
    "INFLUXDB_TOKEN"
)

missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" = "your_long_lived_access_token_here" ] || [ "${!var}" = "admin123" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ The following environment variables need to be configured:"
    for var in "${missing_vars[@]}"; do
        echo "   - $var"
    done
    echo "Please edit the .env file with your production values"
    exit 1
fi

# Build and start production environment
echo "Building and starting production environment..."
docker-compose -f docker-compose.prod.yml up --build -d

echo "Production environment started!"
echo ""
echo "Services available at:"
echo "- Admin API: http://localhost:8000"
echo "- InfluxDB: http://localhost:8086"
echo "- Health checks: http://localhost:8000/health"
echo ""
echo "To view logs, run: ./scripts/view-logs.sh"
echo "To stop services, run: docker-compose -f docker-compose.prod.yml down"
