# Deploy HA Ingestor with Nabu Casa fallback support
param(
    [string]$NabuCasaToken = $env:NABU_CASA_TOKEN,
    [bool]$UseFallback = $true
)

Write-Host "🚀 Deploying HA Ingestor with Nabu Casa Fallback Support" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green

# Check if NABU_CASA_TOKEN is set
if (-not $NabuCasaToken) {
    Write-Host "⚠️  Warning: NABU_CASA_TOKEN environment variable is not set" -ForegroundColor Yellow
    Write-Host "   The service will run with HA Simulator only (no fallback)" -ForegroundColor Yellow
    Write-Host "   To enable Nabu Casa fallback, set:" -ForegroundColor Yellow
    Write-Host "   `$env:NABU_CASA_TOKEN = 'your_long_lived_access_token_here'" -ForegroundColor Yellow
    Write-Host ""
}

# Check if we want to use the enhanced websocket service
if ($UseFallback) {
    Write-Host "🔄 Using enhanced websocket service with fallback support" -ForegroundColor Cyan
    $env:WEBSOCKET_SERVICE_COMMAND = "python src/websocket_with_fallback.py"
} else {
    Write-Host "📡 Using standard websocket service" -ForegroundColor Cyan
    $env:WEBSOCKET_SERVICE_COMMAND = "python src/simple_websocket.py"
}

# Deploy the services
Write-Host "🐳 Starting Docker Compose services..." -ForegroundColor Blue
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check service status
Write-Host "📊 Checking service status..." -ForegroundColor Blue
docker-compose -f docker-compose.dev.yml ps

# Test the connections
Write-Host "🧪 Testing connections..." -ForegroundColor Blue
if ($NabuCasaToken) {
    Write-Host "Testing Nabu Casa connection..." -ForegroundColor Cyan
    python tests/run_nabu_casa_test.py $NabuCasaToken
}

Write-Host "✅ Deployment completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Service URLs:" -ForegroundColor White
Write-Host "  - Health Dashboard: http://localhost:3000" -ForegroundColor White
Write-Host "  - Admin API: http://localhost:8003" -ForegroundColor White
Write-Host "  - InfluxDB: http://localhost:8086" -ForegroundColor White
Write-Host "  - HA Simulator: http://localhost:8123" -ForegroundColor White
Write-Host ""
Write-Host "🔍 To check logs:" -ForegroundColor White
Write-Host "  docker-compose -f docker-compose.dev.yml logs -f websocket-ingestion" -ForegroundColor White
Write-Host ""
Write-Host "🔄 To test fallback functionality:" -ForegroundColor White
Write-Host "  python tests/test_fallback_functionality.py" -ForegroundColor White
