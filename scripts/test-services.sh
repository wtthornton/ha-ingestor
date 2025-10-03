#!/bin/bash

# Service Testing Script
# This script tests all services to ensure they're working correctly

set -e

echo "HA Ingestor Service Testing"
echo "============================"

# Function to test a service endpoint
test_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo "Testing $service_name at $url..."
    
    if curl -f -s "$url" > /dev/null; then
        echo "✅ $service_name is healthy"
        return 0
    else
        echo "❌ $service_name is not responding"
        return 1
    fi
}

# Function to test InfluxDB
test_influxdb() {
    echo "Testing InfluxDB..."
    
    if curl -f -s "http://localhost:8086/health" > /dev/null; then
        echo "✅ InfluxDB is healthy"
        return 0
    else
        echo "❌ InfluxDB is not responding"
        return 1
    fi
}

# Test all services
echo "Testing all services..."
echo ""

failed_tests=0

# Test InfluxDB
if ! test_influxdb; then
    ((failed_tests++))
fi

# Test Admin API
if ! test_service "Admin API" "http://localhost:8003/health"; then
    ((failed_tests++))
fi

# Test WebSocket Ingestion (internal)
if ! test_service "WebSocket Ingestion" "http://localhost:8001/health"; then
    ((failed_tests++))
fi

# Test Weather API (internal)
if ! test_service "Weather API" "http://localhost:8001/health"; then
    ((failed_tests++))
fi

# Test Data Retention Service
if ! test_service "Data Retention Service" "http://localhost:8080/health"; then
    ((failed_tests++))
fi

echo ""
if [ $failed_tests -eq 0 ]; then
    echo "🎉 All services are healthy!"
    exit 0
else
    echo "❌ $failed_tests service(s) failed health checks"
    echo "Check the logs with: ./scripts/view-logs.sh"
    exit 1
fi
