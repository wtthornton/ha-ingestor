#!/bin/bash
"""
Deploy HA Ingestor with Nabu Casa fallback support
"""

set -e

echo "🚀 Deploying HA Ingestor with Nabu Casa Fallback Support"
echo "========================================================"

# Check if NABU_CASA_TOKEN is set
if [ -z "$NABU_CASA_TOKEN" ]; then
    echo "⚠️  Warning: NABU_CASA_TOKEN environment variable is not set"
    echo "   The service will run with HA Simulator only (no fallback)"
    echo "   To enable Nabu Casa fallback, set:"
    echo "   export NABU_CASA_TOKEN=your_long_lived_access_token_here"
    echo ""
fi

# Check if we want to use the enhanced websocket service
USE_FALLBACK=${USE_FALLBACK:-true}

if [ "$USE_FALLBACK" = "true" ]; then
    echo "🔄 Using enhanced websocket service with fallback support"
    
    # Update the docker-compose command to use the enhanced service
    export WEBSOCKET_SERVICE_COMMAND="python src/websocket_with_fallback.py"
else
    echo "📡 Using standard websocket service"
    export WEBSOCKET_SERVICE_COMMAND="python src/simple_websocket.py"
fi

# Deploy the services
echo "🐳 Starting Docker Compose services..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service status
echo "📊 Checking service status..."
docker-compose -f docker-compose.dev.yml ps

# Test the connections
echo "🧪 Testing connections..."
if [ -n "$NABU_CASA_TOKEN" ]; then
    echo "Testing Nabu Casa connection..."
    python tests/run_nabu_casa_test.py "$NABU_CASA_TOKEN"
fi

echo "✅ Deployment completed!"
echo ""
echo "📋 Service URLs:"
echo "  - Health Dashboard: http://localhost:3000"
echo "  - Admin API: http://localhost:8003"
echo "  - InfluxDB: http://localhost:8086"
echo "  - HA Simulator: http://localhost:8123"
echo ""
echo "🔍 To check logs:"
echo "  docker-compose -f docker-compose.dev.yml logs -f websocket-ingestion"
echo ""
echo "🔄 To test fallback functionality:"
echo "  python tests/test_fallback_functionality.py"
