#!/bin/bash
"""
Deploy HA Ingestor with Enhanced Fallback using BMAD Context7 KB patterns
"""

set -e

echo "🚀 Deploying HA Ingestor with Enhanced Fallback (Context7 KB Patterns)"
echo "======================================================================"

# Check if NABU_CASA_TOKEN is set
if [ -z "$NABU_CASA_TOKEN" ]; then
    echo "⚠️  Warning: NABU_CASA_TOKEN environment variable is not set"
    echo "   The service will run with HA Simulator only (no fallback)"
    echo "   To enable Nabu Casa fallback, set:"
    echo "   export NABU_CASA_TOKEN=your_long_lived_access_token_here"
    echo ""
fi

# Check if we want to use the enhanced websocket service
USE_ENHANCED_FALLBACK=${USE_ENHANCED_FALLBACK:-true}

if [ "$USE_ENHANCED_FALLBACK" = "true" ]; then
    echo "🔄 Using enhanced websocket service with Context7 KB patterns"
    echo "📚 Features:"
    echo "   - Optimized WebSocket connections with proper timeouts"
    echo "   - Enhanced authentication using Home Assistant patterns"
    echo "   - Comprehensive connection statistics and monitoring"
    echo "   - Intelligent fallback with priority-based connection management"
    echo "   - Health monitoring with detailed metrics"
    echo ""
    
    # Update the docker-compose command to use the enhanced service
    export WEBSOCKET_SERVICE_COMMAND="python src/websocket_fallback_enhanced.py"
else
    echo "📡 Using standard websocket service"
    export WEBSOCKET_SERVICE_COMMAND="python src/simple_websocket.py"
fi

# Deploy the services
echo "🐳 Starting Docker Compose services with enhanced fallback..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service status
echo "📊 Checking service status..."
docker-compose -f docker-compose.dev.yml ps

# Test the connections
echo "🧪 Testing enhanced connections..."
if [ -n "$NABU_CASA_TOKEN" ]; then
    echo "Testing Nabu Casa connection with Context7 KB patterns..."
    python tests/test_enhanced_fallback.py
else
    echo "Testing HA Simulator connection..."
    python tests/test_enhanced_fallback.py
fi

# Show health status
echo "🏥 Checking enhanced health status..."
sleep 5
curl -s http://localhost:8000/health | python -m json.tool || echo "Health endpoint not ready yet"

echo "✅ Enhanced deployment completed!"
echo ""
echo "📋 Service URLs:"
echo "  - Health Dashboard: http://localhost:3000"
echo "  - Admin API: http://localhost:8003"
echo "  - InfluxDB: http://localhost:8086"
echo "  - HA Simulator: http://localhost:8123"
echo "  - Enhanced WebSocket Health: http://localhost:8000/health"
echo ""
echo "🔍 To check enhanced logs:"
echo "  docker-compose -f docker-compose.dev.yml logs -f websocket-ingestion"
echo ""
echo "🔄 To test enhanced fallback functionality:"
echo "  python tests/test_enhanced_fallback.py"
echo ""
echo "📊 To view detailed connection statistics:"
echo "  curl http://localhost:8000/health | python -m json.tool"
echo ""
echo "🎯 Enhanced Features:"
echo "  - Context7 KB optimized WebSocket connections"
echo "  - Intelligent fallback with priority management"
echo "  - Comprehensive connection statistics"
echo "  - Enhanced authentication patterns"
echo "  - Detailed health monitoring"
echo "  - Optimized timeout and heartbeat settings"
