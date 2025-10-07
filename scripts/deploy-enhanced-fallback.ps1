# Deploy HA Ingestor with Enhanced Fallback using BMAD Context7 KB patterns
param(
    [string]$NabuCasaToken = $env:NABU_CASA_TOKEN,
    [bool]$UseEnhancedFallback = $true
)

Write-Host "🚀 Deploying HA Ingestor with Enhanced Fallback (Context7 KB Patterns)" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green

# Check if NABU_CASA_TOKEN is set
if (-not $NabuCasaToken) {
    Write-Host "⚠️  Warning: NABU_CASA_TOKEN environment variable is not set" -ForegroundColor Yellow
    Write-Host "   The service will run with HA Simulator only (no fallback)" -ForegroundColor Yellow
    Write-Host "   To enable Nabu Casa fallback, set:" -ForegroundColor Yellow
    Write-Host "   `$env:NABU_CASA_TOKEN = 'your_long_lived_access_token_here'" -ForegroundColor Yellow
    Write-Host ""
}

# Check if we want to use the enhanced websocket service
if ($UseEnhancedFallback) {
    Write-Host "🔄 Using enhanced websocket service with Context7 KB patterns" -ForegroundColor Cyan
    Write-Host "📚 Features:" -ForegroundColor White
    Write-Host "   - Optimized WebSocket connections with proper timeouts" -ForegroundColor White
    Write-Host "   - Enhanced authentication using Home Assistant patterns" -ForegroundColor White
    Write-Host "   - Comprehensive connection statistics and monitoring" -ForegroundColor White
    Write-Host "   - Intelligent fallback with priority-based connection management" -ForegroundColor White
    Write-Host "   - Health monitoring with detailed metrics" -ForegroundColor White
    Write-Host ""
    
    $env:WEBSOCKET_SERVICE_COMMAND = "python src/websocket_fallback_enhanced.py"
} else {
    Write-Host "📡 Using standard websocket service" -ForegroundColor Cyan
    $env:WEBSOCKET_SERVICE_COMMAND = "python src/simple_websocket.py"
}

# Deploy the services
Write-Host "🐳 Starting Docker Compose services with enhanced fallback..." -ForegroundColor Blue
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check service status
Write-Host "📊 Checking service status..." -ForegroundColor Blue
docker-compose -f docker-compose.dev.yml ps

# Test the connections
Write-Host "🧪 Testing enhanced connections..." -ForegroundColor Blue
if ($NabuCasaToken) {
    Write-Host "Testing Nabu Casa connection with Context7 KB patterns..." -ForegroundColor Cyan
    python tests/test_enhanced_fallback.py
} else {
    Write-Host "Testing HA Simulator connection..." -ForegroundColor Cyan
    python tests/test_enhanced_fallback.py
}

# Show health status
Write-Host "🏥 Checking enhanced health status..." -ForegroundColor Blue
Start-Sleep -Seconds 5
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    $healthResponse | ConvertTo-Json -Depth 10
} catch {
    Write-Host "Health endpoint not ready yet" -ForegroundColor Yellow
}

Write-Host "✅ Enhanced deployment completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Service URLs:" -ForegroundColor White
Write-Host "  - Health Dashboard: http://localhost:3000" -ForegroundColor White
Write-Host "  - Admin API: http://localhost:8003" -ForegroundColor White
Write-Host "  - InfluxDB: http://localhost:8086" -ForegroundColor White
Write-Host "  - HA Simulator: http://localhost:8123" -ForegroundColor White
Write-Host "  - Enhanced WebSocket Health: http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "🔍 To check enhanced logs:" -ForegroundColor White
Write-Host "  docker-compose -f docker-compose.dev.yml logs -f websocket-ingestion" -ForegroundColor White
Write-Host ""
Write-Host "🔄 To test enhanced fallback functionality:" -ForegroundColor White
Write-Host "  python tests/test_enhanced_fallback.py" -ForegroundColor White
Write-Host ""
Write-Host "📊 To view detailed connection statistics:" -ForegroundColor White
Write-Host "  Invoke-RestMethod -Uri 'http://localhost:8000/health' | ConvertTo-Json -Depth 10" -ForegroundColor White
Write-Host ""
Write-Host "🎯 Enhanced Features:" -ForegroundColor White
Write-Host "  - Context7 KB optimized WebSocket connections" -ForegroundColor White
Write-Host "  - Intelligent fallback with priority management" -ForegroundColor White
Write-Host "  - Comprehensive connection statistics" -ForegroundColor White
Write-Host "  - Enhanced authentication patterns" -ForegroundColor White
Write-Host "  - Detailed health monitoring" -ForegroundColor White
Write-Host "  - Optimized timeout and heartbeat settings" -ForegroundColor White
